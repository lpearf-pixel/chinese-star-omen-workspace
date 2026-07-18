from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import typer
except ModuleNotFoundError:  # pragma: no cover
    typer = None

try:
    from jsonschema import validate
except ModuleNotFoundError:  # pragma: no cover

    def validate(instance, schema):
        for key in schema.get("required", []):
            if key not in instance:
                raise ValueError(f"Missing required field: {key}")


from src.candidate_cards import generate_candidate_cards, sync_upstream_status
from src.config.settings import get_settings
from src.connectors.evidence_resolver import resolve_evidence
from src.connectors.kb_contract import (
    STAGE1_RECALL_CARD_TYPES,
    STAGE2_PRIMARY_CARD_TYPES,
    is_citable_evidence,
)
from src.connectors.kb_search_retriever import KBSearchRetriever
from src.connectors.manifest_reader import ManifestReader
from src.eval.corpus_eval import run_corpus_eval
from src.research import build_case_report, build_research_index, validate_research_data
from src.rule_engine.minimal_matcher import run_match_rule

app = typer.Typer(help="Chinese astro model CLI") if typer else None


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_data_impl(
    rules_path: Path = Path("data/processed/corpus/sample_rules.json"),
    asterism_path: Path = Path("data/processed/ontology/sample_asterisms.json"),
    rule_schema: Path = Path("schemas/omen_rule.schema.json"),
    asterism_schema: Path = Path("schemas/asterism.schema.json"),
):
    rules = _load_json(rules_path)
    rule_schema_obj = _load_json(rule_schema)
    for rule in rules:
        validate(instance=rule, schema=rule_schema_obj)
    asterisms = _load_json(asterism_path)
    asterism_schema_obj = _load_json(asterism_schema)
    for item in asterisms:
        validate(instance=item, schema=asterism_schema_obj)
    return {"ok": True, "rules": len(rules), "asterisms": len(asterisms)}


def _split_hits(result: dict[str, Any], *, include_raw: bool = False) -> dict[str, Any]:
    filtered_hits = result.get("hits", [])
    structured_types = {card.value for card in STAGE1_RECALL_CARD_TYPES}
    primary_types = {card.value for card in STAGE2_PRIMARY_CARD_TYPES}
    structured = [
        hit for hit in filtered_hits if hit.get("card_type") in structured_types
    ]
    primary = [hit for hit in filtered_hits if hit.get("card_type") in primary_types]
    payload = {
        "normalized_query": result.get("normalized_query"),
        "query_variants": result.get("query_variants", []),
        "exact_hits": result.get("exact_hits", []),
        "related_hits": result.get("related_hits", []),
        "structured_hits": structured,
        "primary_hits": primary,
        "primary_candidates": result.get("primary_candidates", []),
        "structured_fallbacks": result.get("structured_fallbacks", []),
        "fallback_used": result.get("fallback_used", False),
        "files_scanned": result.get("files_scanned", 0),
        "matched_files": result.get("matched_files", []),
        "matched_headings": result.get("matched_headings", []),
        "matched_quotes": result.get("matched_quotes", []),
    }
    if "debug_scan" in result:
        payload["debug_scan"] = result.get("debug_scan")
    if include_raw:
        payload["raw_hits"] = result.get("raw_hits", [])
        payload["inferred_hits"] = result.get("inferred_hits", [])
        payload["filtered_hits"] = filtered_hits
    return payload


def inspect_kb_impl(
    root: Path | None = None,
    query: str | None = None,
    book_id: str | None = None,
    card_type: list[str] | None = None,
    evidence_level: str | None = None,
    limit: int | None = None,
    show_raw: bool = False,
    base_url: str | None = None,
    api_key: str | None = None,
    collection: str | None = None,
    show_related: bool = False,
    query_mode: str | None = None,
    literal_first: bool | None = None,
):
    settings = get_settings()
    effective_limit = limit if limit is not None else settings.app_default_limit
    if query:
        retriever = KBSearchRetriever(base_url=base_url, api_key=api_key)
        filters: dict[str, Any] = {}
        if book_id:
            filters["kb_book_id"] = book_id
        if card_type:
            filters["card_type"] = card_type
        if evidence_level:
            filters["evidence_level"] = evidence_level
        try:
            stage = retriever.two_stage_retrieve(
                query,
                top_k=effective_limit,
                limit=effective_limit,
                collection=collection,
                filters=filters or None,
                query_mode=query_mode,
                literal_first=literal_first,
            )
        except Exception as exc:
            return {
                "mode": "search",
                "query": query,
                "root": str(root) if root else None,
                "error": str(exc),
                "hint": (
                    "check KB_SEARCH_API_KEY, KB_SEARCH_BASE_URL/"
                    "KB_SEARCH_API_PORT, and whether kb-search service is running"
                ),
            }

        stage1_raw = stage.get("stage1", {})
        stage2_raw = stage.get("stage2", {})
        stage1_out = _split_hits(stage1_raw, include_raw=show_raw)
        stage2_out = _split_hits(stage2_raw, include_raw=show_raw)
        top_hit = (
            stage1_raw.get("hits")
            or stage1_raw.get("inferred_hits")
            or stage2_raw.get("hits")
            or [None]
        )[0]
        effective_mode = stage1_raw.get("query_mode", query_mode or "knowledge")

        if effective_mode == "knowledge":
            stage1_out["exact_hits"] = stage1_out.get("exact_hits", [])[:1]
            stage1_out["related_hits"] = (
                stage1_out.get("related_hits", [])[:3] if show_related else []
            )
        elif (
            effective_mode == "evidence"
            and not stage2_out.get("structured_fallbacks")
            and not stage2_out.get("primary_hits")
            and not stage2_out.get("primary_candidates")
        ):
            fallback_pool: list[dict[str, Any]] = []
            for key in ("exact_hits", "related_hits", "structured_hits"):
                fallback_pool.extend(stage1_out.get(key, []))
            fallback_pool.extend(stage1_raw.get("hits", []))

            deduped: list[dict[str, Any]] = []
            seen: set[str] = set()
            for hit in fallback_pool:
                if hit.get("evidence_level") != "structured":
                    continue
                dedup_key = str(
                    hit.get("chunk_id")
                    or hit.get("path")
                    or hit.get("title")
                    or repr(hit)
                )
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)
                deduped.append({**hit, "status": "candidate_only"})
            stage2_out["structured_fallbacks"] = deduped

        stage2_out["primary_candidates"] = stage2_out.get(
            "primary_candidates", []
        )
        stage2_out["structured_fallbacks"] = stage2_out.get(
            "structured_fallbacks", []
        )

        top_book_id = None
        if isinstance(top_hit, dict):
            top_book_id = top_hit.get("kb_book_id") or top_hit.get("book_id")
        out = {
            "mode": "search",
            "query": query,
            "query_mode": effective_mode,
            "normalized_query": stage1_out.get("normalized_query"),
            "query_variants": stage1_out.get("query_variants", []),
            "root": str(root) if root else None,
            "book_title": (
                top_hit.get("book_title") if isinstance(top_hit, dict) else None
            ),
            "book_id": top_book_id,
            "kb_book_id": top_book_id,
            "exact_hits": stage1_out.get("exact_hits", []),
            "related_hits": stage1_out.get("related_hits", []),
            "primary_candidates": stage2_out.get("primary_candidates", []),
            "structured_fallbacks": stage2_out.get("structured_fallbacks", []),
            "stage1": stage1_out,
            "stage2": stage2_out,
            "note": (
                "if no primary hits, output should be treated as clue/"
                "candidate explanation only"
            ),
        }
        if show_raw:
            out["raw"] = stage
        return out

    if root:
        reader = ManifestReader(root)
        return {"mode": "local_check", "result": reader.inspect_root()}

    return {
        "mode": "noop",
        "message": "provide --query for kb-search or --root for local inspection",
    }


def generate_candidate_card_impl(
    query: str,
    book_id: str,
    out_dir: Path,
    base_url: str | None = None,
):
    return generate_candidate_cards(query, book_id, out_dir, base_url=base_url)


def sync_upstream_status_impl(book_id: str, candidate_root: Path, base_url: str):
    return sync_upstream_status(book_id, candidate_root, base_url)


def validate_research_data_impl(
    research_root: Path = Path("data/research"),
    rules_path: Path = Path("data/processed/corpus/sample_rules.json"),
):
    return validate_research_data(research_root=research_root, rules_path=rules_path)


def generate_case_report_impl(
    correlation_id: str | None = None,
    correlation_file: Path | None = None,
    research_root: Path = Path("data/research"),
    rules_path: Path = Path("data/processed/corpus/sample_rules.json"),
    out_dir: Path = Path("data/research/case_reports"),
):
    return build_case_report(
        correlation_id=correlation_id,
        correlation_file=correlation_file,
        research_root=research_root,
        rules_path=rules_path,
        out_dir=out_dir,
    )


def build_research_index_impl(research_root: Path = Path("data/research")):
    return build_research_index(research_root=research_root)


def resolve_evidence_impl(
    rule: Path,
    kb_root: Path | None = None,
    strict: bool = False,
):
    settings = get_settings()
    rule_obj = _load_json(rule)
    if isinstance(rule_obj, list):
        if not rule_obj:
            raise ValueError("rule file is an empty array")
        rule_obj = rule_obj[0]
    if not isinstance(rule_obj, dict):
        raise ValueError("rule file must contain a JSON object")

    evidence = rule_obj.get("evidence")
    if not isinstance(evidence, dict):
        raise ValueError("rule file has no evidence")

    effective_root = kb_root if kb_root else Path(settings.kb_sources_root)
    resolved = resolve_evidence(evidence, effective_root)
    payload = {"rule_id": rule_obj.get("id"), **resolved}
    if strict and payload.get("status") != "citable":
        status = str(payload.get("status") or "unknown")
        reason = str(payload.get("candidate_reason") or "validation_failed")
        raise ValueError(
            f"evidence is not citable: status={status} reason={reason}"
        )
    return payload


def audit_rules_impl(
    rules_path: Path = Path("data/processed/corpus/sample_rules.json"),
    kb_root: Path | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    rules = _load_json(rules_path)
    if not isinstance(rules, list):
        raise ValueError("rules file must be a JSON array")

    effective_root = kb_root or Path(settings.kb_sources_root)
    report: dict[str, Any] = {
        "total_rules": len(rules),
        "citable": 0,
        "candidate_only": 0,
        "missing_evidence": 0,
        "status_counts": {},
        "details": [],
    }

    for rule in rules:
        rule_id = rule.get("id", "<unknown>") if isinstance(rule, dict) else "<unknown>"
        evidence = rule.get("evidence") if isinstance(rule, dict) else None
        if not isinstance(evidence, dict):
            status = "missing_evidence"
            detail = {
                "rule_id": rule_id,
                "status": status,
                "candidate_reason": "rule_has_no_evidence",
                "trace": None,
            }
            report["missing_evidence"] += 1
        else:
            resolved = resolve_evidence(evidence, effective_root)
            status = str(resolved.get("status") or "candidate_only")
            detail = {
                "rule_id": rule_id,
                "status": status,
                "candidate_reason": resolved.get("candidate_reason"),
                "card_type": resolved.get("card_type"),
                "relative_path": resolved.get("relative_path"),
                "source_locator": resolved.get("source_locator"),
                "page_marker": resolved.get("page_marker"),
                "paragraph_index": resolved.get("paragraph_index"),
                "trace": resolved.get("trace"),
            }
            if is_citable_evidence(resolved):
                report["citable"] += 1
            elif status == "candidate_only":
                report["candidate_only"] += 1

        status_counts = report["status_counts"]
        status_counts[status] = int(status_counts.get(status, 0)) + 1
        report["details"].append(detail)

    report["status_counts"] = dict(sorted(report["status_counts"].items()))
    return report


if typer:

    @app.command("validate-data")
    def validate_data(
        rules_path: Path = Path("data/processed/corpus/sample_rules.json"),
        asterism_path: Path = Path("data/processed/ontology/sample_asterisms.json"),
        rule_schema: Path = Path("schemas/omen_rule.schema.json"),
        asterism_schema: Path = Path("schemas/asterism.schema.json"),
    ):
        out = validate_data_impl(
            rules_path,
            asterism_path,
            rule_schema,
            asterism_schema,
        )
        typer.echo(
            f"Validation passed: {out['rules']} rules, "
            f"{out['asterisms']} asterisms"
        )

    @app.command("inspect-kb")
    def inspect_kb(
        root: Path | None = typer.Option(None, "--root"),
        query: str | None = typer.Option(None, "--query"),
        book_id: str | None = typer.Option(None, "--book-id"),
        card_type: list[str] | None = typer.Option(None, "--card-type"),
        evidence_level: str | None = typer.Option(None, "--evidence-level"),
        limit: int | None = typer.Option(None, "--limit"),
        collection: str | None = typer.Option(None, "--collection"),
        base_url: str | None = typer.Option(None, "--base-url"),
        api_key: str | None = typer.Option(None, "--api-key"),
        show_related: bool = typer.Option(False, "--show-related"),
        show_raw: bool = typer.Option(False, "--show-raw"),
        query_mode: str | None = typer.Option(None, "--query-mode"),
        literal_first: bool | None = typer.Option(None, "--literal-first"),
    ):
        out = inspect_kb_impl(
            root,
            query,
            book_id,
            card_type,
            evidence_level,
            limit,
            show_raw,
            base_url,
            api_key,
            collection,
            show_related,
            query_mode,
            literal_first,
        )
        typer.echo(json.dumps(out, ensure_ascii=False, indent=2))

    @app.command("resolve-evidence")
    def resolve_evidence_cmd(
        rule: Path = typer.Option(..., "--rule"),
        kb_root: Path | None = typer.Option(None, "--kb-root"),
        pretty: bool = typer.Option(False, "--pretty"),
        strict: bool = typer.Option(False, "--strict"),
    ):
        out = resolve_evidence_impl(rule, kb_root=kb_root, strict=strict)
        if pretty:
            typer.echo("\n".join(f"{key}: {value}" for key, value in out.items()))
            if out["status"] != "citable":
                typer.echo(
                    "当前证据不可作为最终引用："
                    f"status={out.get('status')} "
                    f"reason={out.get('candidate_reason')}"
                )
        else:
            typer.echo(json.dumps(out, ensure_ascii=False, indent=2))

    @app.command("search-kb")
    def search_kb(
        query: str,
        book_id: str | None = None,
        card_type: list[str] | None = None,
        evidence_level: str | None = None,
        top_k: int | None = None,
        collection: str | None = None,
        query_mode: str | None = None,
        literal_first: bool | None = None,
        literal_pool_factor: int | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ):
        retriever = KBSearchRetriever(base_url=base_url, api_key=api_key)
        filters: dict[str, Any] = {}
        if book_id:
            filters["kb_book_id"] = book_id
        if card_type:
            filters["card_type"] = card_type
        if evidence_level:
            filters["evidence_level"] = evidence_level
        result = retriever.search(
            query,
            top_k=top_k,
            limit=top_k,
            collection=collection,
            filters=filters or None,
            query_mode=query_mode,
            literal_first=literal_first,
            literal_pool_factor=literal_pool_factor,
        )
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))

    @app.command("audit-rules")
    def audit_rules(
        rules_path: Path = Path("data/processed/corpus/sample_rules.json"),
        kb_root: Path | None = None,
    ):
        try:
            report = audit_rules_impl(rules_path, kb_root)
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc
        typer.echo(json.dumps(report, ensure_ascii=False, indent=2))

    @app.command("generate-candidate-card")
    def generate_candidate_card(
        query: str = typer.Option(..., "--query"),
        book_id: str = typer.Option(..., "--book-id"),
        out_dir: Path = typer.Option(..., "--out-dir"),
        base_url: str | None = typer.Option(None, "--base-url"),
    ):
        out = generate_candidate_card_impl(query, book_id, out_dir, base_url)
        typer.echo(json.dumps(out, ensure_ascii=False, indent=2))
        typer.echo(
            "candidate cards generated; submit to upstream "
            "Local-KB-Unified after review."
        )

    @app.command("sync-upstream-status")
    def sync_upstream_status_cmd(
        book_id: str = typer.Option(..., "--book-id"),
        candidate_root: Path = typer.Option(
            Path("data/generated_candidates"),
            "--candidate-root",
        ),
        base_url: str = typer.Option(
            "http://127.0.0.1:8008",
            "--base-url",
        ),
    ):
        out = sync_upstream_status_impl(book_id, candidate_root, base_url)
        typer.echo(json.dumps(out, ensure_ascii=False, indent=2))

    @app.command("validate-research-data")
    def validate_research_data_cmd(
        research_root: Path = typer.Option(
            Path("data/research"),
            "--research-root",
        ),
        rules_path: Path = typer.Option(
            Path("data/processed/corpus/sample_rules.json"),
            "--rules-path",
        ),
        output_format: str = typer.Option("json", "--format"),
    ):
        out = validate_research_data_impl(research_root, rules_path)
        if output_format == "text":
            typer.echo(
                f"ok={out['ok']} celestial={out['celestial_events_count']} "
                f"historical={out['historical_events_count']} "
                f"correlations={out['correlations_count']}"
            )
            for error in out["errors"]:
                typer.echo(f"ERROR: {error}")
            for warning in out["warnings"]:
                typer.echo(f"WARNING: {warning}")
        else:
            typer.echo(json.dumps(out, ensure_ascii=False, indent=2))
        if not out["ok"]:
            raise typer.Exit(code=1)

    @app.command("generate-case-report")
    def generate_case_report_cmd(
        correlation_id: str | None = typer.Option(None, "--correlation-id"),
        correlation_file: Path | None = typer.Option(None, "--correlation-file"),
        research_root: Path = typer.Option(
            Path("data/research"),
            "--research-root",
        ),
        rules_path: Path = typer.Option(
            Path("data/processed/corpus/sample_rules.json"),
            "--rules-path",
        ),
        out_dir: Path = typer.Option(
            Path("data/research/case_reports"),
            "--out-dir",
        ),
        output_format: str = typer.Option("markdown", "--format"),
    ):
        if output_format != "markdown":
            raise typer.BadParameter("only --format markdown is supported")
        out = generate_case_report_impl(
            correlation_id,
            correlation_file,
            research_root,
            rules_path,
            out_dir,
        )
        typer.echo(
            json.dumps(
                {key: value for key, value in out.items() if key != "case_report"},
                ensure_ascii=False,
                indent=2,
            )
        )

    @app.command("build-research-index")
    def build_research_index_cmd(
        research_root: Path = typer.Option(
            Path("data/research"),
            "--research-root",
        ),
    ):
        out = build_research_index_impl(research_root)
        typer.echo(json.dumps(out, ensure_ascii=False, indent=2))

    @app.command("eval-corpus")
    def eval_corpus(
        eval_path: Path = typer.Option(
            Path("eval/corpus_eval_cases.yaml"),
            "--eval-path",
        ),
        collection: str | None = typer.Option(None, "--collection"),
        top_k: int | None = typer.Option(None, "--top-k"),
        base_url: str | None = typer.Option(None, "--base-url"),
        api_key: str | None = typer.Option(None, "--api-key"),
    ):
        retriever = KBSearchRetriever(base_url=base_url, api_key=api_key)
        out = run_corpus_eval(
            eval_path=eval_path,
            retriever=retriever,
            collection=collection,
            top_k=top_k,
        )
        typer.echo(json.dumps(out, ensure_ascii=False, indent=2))

    @app.command("match-rule")
    def match_rule(
        event: Path = typer.Option(..., "--event"),
        rules_path: Path = typer.Option(
            Path("data/processed/corpus/sample_rules.json"),
            "--rules-path",
        ),
        kb_root: Path | None = typer.Option(None, "--kb-root"),
    ):
        out = run_match_rule(
            event_path=event,
            rules_path=rules_path,
            kb_root=kb_root,
        )
        typer.echo(json.dumps(out, ensure_ascii=False, indent=2))


def _main_fallback():  # pragma: no cover
    parser = argparse.ArgumentParser(description="Chinese astro model CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate-data")

    inspect_parser = sub.add_parser("inspect-kb")
    inspect_parser.add_argument("--root")
    inspect_parser.add_argument("--query")
    inspect_parser.add_argument("--book-id")
    inspect_parser.add_argument("--card-type", action="append")
    inspect_parser.add_argument("--evidence-level")
    inspect_parser.add_argument("--limit", type=int, default=None)
    inspect_parser.add_argument("--collection")
    inspect_parser.add_argument("--base-url")
    inspect_parser.add_argument("--api-key")
    inspect_parser.add_argument("--show-related", action="store_true")
    inspect_parser.add_argument("--show-raw", action="store_true")
    inspect_parser.add_argument("--query-mode")
    inspect_parser.add_argument("--literal-first", action="store_true")

    resolve_parser = sub.add_parser("resolve-evidence")
    resolve_parser.add_argument("--rule", required=True)
    resolve_parser.add_argument("--kb-root")
    resolve_parser.add_argument("--pretty", action="store_true")
    resolve_parser.add_argument("--strict", action="store_true")

    generate_parser = sub.add_parser("generate-candidate-card")
    generate_parser.add_argument("--query", required=True)
    generate_parser.add_argument("--book-id", required=True)
    generate_parser.add_argument("--out-dir", required=True)
    generate_parser.add_argument("--base-url")

    sync_parser = sub.add_parser("sync-upstream-status")
    sync_parser.add_argument("--book-id", required=True)
    sync_parser.add_argument(
        "--candidate-root",
        default="data/generated_candidates",
    )
    sync_parser.add_argument("--base-url", default="http://127.0.0.1:8008")

    audit_parser = sub.add_parser("audit-rules")
    audit_parser.add_argument(
        "--rules-path",
        default="data/processed/corpus/sample_rules.json",
    )
    audit_parser.add_argument("--kb-root")

    eval_parser = sub.add_parser("eval-corpus")
    eval_parser.add_argument("--eval-path", default="eval/corpus_eval_cases.yaml")
    eval_parser.add_argument("--collection")
    eval_parser.add_argument("--top-k", type=int, default=None)
    eval_parser.add_argument("--base-url")
    eval_parser.add_argument("--api-key")

    match_parser = sub.add_parser("match-rule")
    match_parser.add_argument("--event", required=True)
    match_parser.add_argument(
        "--rules-path",
        default="data/processed/corpus/sample_rules.json",
    )
    match_parser.add_argument("--kb-root")

    args = parser.parse_args()
    if args.cmd == "validate-data":
        out = validate_data_impl()
        print(
            f"Validation passed: {out['rules']} rules, "
            f"{out['asterisms']} asterisms"
        )
    elif args.cmd == "inspect-kb":
        out = inspect_kb_impl(
            Path(args.root) if args.root else None,
            args.query,
            args.book_id,
            args.card_type,
            args.evidence_level,
            args.limit,
            args.show_raw,
            args.base_url,
            args.api_key,
            args.collection,
            args.show_related,
            args.query_mode,
            args.literal_first,
        )
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif args.cmd == "resolve-evidence":
        out = resolve_evidence_impl(
            Path(args.rule),
            Path(args.kb_root) if args.kb_root else None,
            args.strict,
        )
        if args.pretty:
            print("\n".join(f"{key}: {value}" for key, value in out.items()))
        else:
            print(json.dumps(out, ensure_ascii=False, indent=2))
    elif args.cmd == "generate-candidate-card":
        out = generate_candidate_card_impl(
            args.query,
            args.book_id,
            Path(args.out_dir),
            args.base_url,
        )
        print(json.dumps(out, ensure_ascii=False, indent=2))
        print(
            "candidate cards generated; submit to upstream "
            "Local-KB-Unified after review."
        )
    elif args.cmd == "sync-upstream-status":
        out = sync_upstream_status_impl(
            args.book_id,
            Path(args.candidate_root),
            args.base_url,
        )
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif args.cmd == "audit-rules":
        out = audit_rules_impl(
            Path(args.rules_path),
            Path(args.kb_root) if args.kb_root else None,
        )
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif args.cmd == "eval-corpus":
        retriever = KBSearchRetriever(base_url=args.base_url, api_key=args.api_key)
        out = run_corpus_eval(
            eval_path=Path(args.eval_path),
            retriever=retriever,
            collection=args.collection,
            top_k=args.top_k,
        )
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif args.cmd == "match-rule":
        out = run_match_rule(
            event_path=Path(args.event),
            rules_path=Path(args.rules_path),
            kb_root=Path(args.kb_root) if args.kb_root else None,
        )
        print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if typer:
        app()
    else:
        _main_fallback()
