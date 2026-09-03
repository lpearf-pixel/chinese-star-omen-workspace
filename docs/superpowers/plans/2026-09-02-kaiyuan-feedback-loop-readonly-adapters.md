# Kaiyuan Feedback Loop S1 Read-only Adapters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` (recommended) or
> `superpowers:executing-plans` to implement this plan task by task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Status:** APPROVED FOR EXECUTION on 2026-09-02 under the user's standing
authorization to pass subsequent in-scope plans/specifications without another
confirmation pause.

**Goal:** Produce one deterministic, complete episode 22 local-evidence probe
batch through a fail-closed read-only KB path and feed it to the unchanged S0
feedback-loop package builder.

**Architecture:** New S1-only contracts and adapters load bounded local inputs,
pin all local source reads to a caller-supplied snapshot, call the existing
two-stage retriever through a literal-loopback transport, strictly validate raw
responses before fallback, and project only resolver-revalidated passages into
`context_only` / `unresolved` probes. Existing S0 contracts, comparison,
planning and atomic publication remain unchanged.

**Tech Stack:** Python 3.12, Pydantic v2, httpx, pytest, GNU Make, existing
`kb-text-core` passage semantics and `apps/star-omen` feedback-loop package
primitives.

**Spec:**
`docs/superpowers/specs/2026-09-02-kaiyuan-feedback-loop-readonly-adapters-design.md`

## Global Constraints

- Work only on `codex/kaiyuan-feedback-loop-readonly-adapters-v1`, stacked on
  `e087d5e627bcb3e838e49015c61a3f74c0a5a2e8`. Never write stable or `main`.
- Do not modify PR #54, Reviewer A/B material, B10 artifacts, raw corpus,
  `apps/local-kb-unified`, `packages/kb-contracts`, `packages/kb-text-core`,
  Qdrant state or `local_kb_default`.
- Do not call a live platform, model, TTS, renderer, uploader or publisher.
- Keep `contracts_v1.py`, `comparison.py`, `planner.py`, `orchestrator.py` and
  `scripts/run_video_feedback_loop.py` behavior unchanged.
- Never commit a source-snapshot fixture or source bytes. Hermetic tests create
  a temporary KB root and hash-only manifest at runtime.
- A successful S1 probe is always `result_state="unresolved"`; each emitted
  reference is `evidence_class="citable_passage"` and
  `relationship="context_only"`.
- Every retrieval or integrity error fails the whole batch before an S0 build or
  output directory becomes visible.
- Use TDD for every behavior change: write the named failing test, run it and
  observe the expected failure, implement the minimum behavior, rerun focused
  and related regression tests, then commit.
- Treat every code block as a normative interface or selected exact algorithm,
  and every adjacent prose matrix as required implementation behavior. Type
  signatures are not complete bodies: implementation must satisfy the entire
  named test matrix and may not leave an ellipsis, TODO, stub or permissive
  fallback in a production path.
- At the end of every task, record exact test evidence, create one small local
  commit, non-force push only the S1 branch, fetch/read back the remote tree and
  require equality before starting the next task.
- B10 Reviewer B remains a terminal human gate and is not an S1 completion
  dependency.

## Reviewed planning checkpoint

Before the bootstrap clean-worktree assertion, finish the current docs-only
specification/plan review at `0 Critical / 0 Important`, commit the seven
planning/governance files, non-force deliver them to the S1 branch, fetch the
remote ref, require exact tree and single-parent continuity, and safely realign
the local ref if the authorized connector creates a different commit SHA with
the same tree. That reviewed planning checkpoint is not Task 1 and creates no
runtime behavior. Run the bootstrap only from its clean fetched tree.

Create that checkpoint with this executable pre-commit guard:

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
BRANCH=codex/kaiyuan-feedback-loop-readonly-adapters-v1
BASE=fc65e2fbf0eec6652919bfb2b75bb63eee06f64d
S0=e087d5e627bcb3e838e49015c61a3f74c0a5a2e8
git fetch origin "+refs/heads/$BRANCH:refs/remotes/origin/$BRANCH"
test "$(git symbolic-ref --short HEAD)" = "$BRANCH"
test "$(git rev-parse HEAD)" = "$BASE"
test "$(git rev-parse "origin/$BRANCH")" = "$BASE"
git merge-base --is-ancestor "$S0" HEAD
git diff --check
git add docs/development/DECISIONS.md \
  docs/development/PROJECT_MEMORY.md \
  docs/development/TASKS.md \
  docs/development/WORK_LOG.md \
  docs/superpowers/specs/2026-09-02-kaiyuan-feedback-loop-readonly-adapters-design.md \
  docs/superpowers/plans/2026-09-02-kaiyuan-feedback-loop-readonly-adapters.md \
  summary.md
git diff --cached --check
EXPECTED=$(printf '%s\n' \
  docs/development/DECISIONS.md \
  docs/development/PROJECT_MEMORY.md \
  docs/development/TASKS.md \
  docs/development/WORK_LOG.md \
  docs/superpowers/plans/2026-09-02-kaiyuan-feedback-loop-readonly-adapters.md \
  docs/superpowers/specs/2026-09-02-kaiyuan-feedback-loop-readonly-adapters-design.md \
  summary.md)
test "$(git diff --cached --name-only)" = "$EXPECTED"
git commit -m "docs: start readonly adapter execution"
```

## Environment Bootstrap

The worktree `.venv/bin/python3` link was stale and has been repaired. Revalidate
it, and repair only if needed, without changing tracked dependency files:

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
"$CODEX_PRIMARY_RUNTIME_PYTHON" -m venv --upgrade .venv
.venv/bin/python --version
.venv/bin/python -m pytest --version
.venv/bin/python -m pip check
```

Run the inherited baseline before implementation:

```bash
set -euo pipefail
env -u CODEX_PRIMARY_RUNTIME_PYTHON PATH="$PWD/.venv/bin:$PATH" make downstream-test
.venv/bin/python -m unittest discover -s scripts/tests -p 'test_*.py' -v
.venv/bin/python scripts/check_development_governance.py \
  --root . \
  --base e087d5e627bcb3e838e49015c61a3f74c0a5a2e8 \
  --head HEAD
S1_STATUS=$(git status --porcelain)
test -z "$S1_STATUS"
```

Expected baseline: the inherited S0/downstream and governance suites pass and
the tracked worktree is clean. If dependency installation or a baseline gate
fails, apply `superpowers:systematic-debugging`; do not weaken a test or alter
tracked dependency declarations merely to make the environment pass.

Freeze these read-only remote invariants at task entry: `main` is
`98e0bb713a164a384d890b273af47d3b9b444682`, `stable/kaiyuan-v2` is
`99c0a85c1f944add8d013aedbae830fe022b7c3b`, and the unchanged S0 branch
`codex/kaiyuan-evidence-feedback-loop-skeleton-v1` is
`e087d5e627bcb3e838e49015c61a3f74c0a5a2e8`. Connected GitHub readback records
PR #54 as `state=open`, `draft=true`, `merged=false`,
`head=codex/kaiyuan-b10-calibration-v2`,
`head_sha=932f9e68862025bc620e0cf2d439415c5ea37af4` and
`base=stable/kaiyuan-v2`. These are observation guards, not write targets.

---

### Task 1: Add strict S1 contracts and descriptor-stable local JSON inputs

**Files:**

- Create:
  `apps/star-omen/src/video_pipeline/feedback_loop/readonly_contracts_v1.py`
- Create:
  `apps/star-omen/src/video_pipeline/feedback_loop/strict_local_files.py`
- Create:
  `apps/star-omen/tests/video_pipeline/feedback_loop/test_readonly_contracts_v1.py`
- Create:
  `apps/star-omen/tests/video_pipeline/feedback_loop/test_readonly_inputs_v1.py`

**Interfaces:**

- Consumes: existing `ExternalAuditBundleV1`,
  `canonical_contract_bytes(model: BaseModel) -> bytes` and S0 identity fields.
- Produces: `LocalEvidenceProbeRequestV1`, `LocalEvidenceQueryPlanV1`,
  `LocalKBSourceFileV1`, `LocalKBSourceSnapshotV1`, `CorpusVersion`,
  `SourceSnapshotBindingV1`, `ReadOnlyTwoStageRetriever`, `ReadOnlyErrorCode`, `ReadOnlyAdapterError`,
  `StrictJSONDocument[T]`, `load_external_audit_v1(path: Path)`,
  `load_query_plan_v1(path: Path)`, `load_source_snapshot_v1(path: Path)`,
  `bind_production_query_plan_to_audit(plan=, audit_bundle=)`,
  `bind_source_snapshot_to_plan(snapshot=, plan=)` and
  `canonical_contract_sha256(model: BaseModel) -> str`.

- [ ] **Step 1: Write failing contract tests**

Cover the exact v1 models and closed schemas:

```python
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal, Mapping, Protocol, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)
from src.video_pipeline.contracts._common import Sha256Hex, StableId


def _reject_corpus_version_preprocessing(value: object) -> object:
    if not isinstance(value, str):
        raise ValueError("corpus version must be a string")
    if value != value.strip() or any(
        character.isspace() or ord(character) < 0x20 or ord(character) == 0x7F
        for character in value
    ):
        raise ValueError("corpus version must not contain whitespace or controls")
    return value


def _validate_corpus_version(value: str) -> str:
    for format_string in ("%Y%m%dT%H%M%SZ", "%Y-%m-%dT%H%M%SZ"):
        try:
            parsed = datetime.strptime(value, format_string)
        except ValueError:
            continue
        if parsed.strftime(format_string) == value:
            return value
    raise ValueError("corpus version must be a canonical producer timestamp")


CorpusVersion = Annotated[
    str,
    BeforeValidator(_reject_corpus_version_preprocessing),
    StringConstraints(
        strict=True,
        pattern=r"^(?:[0-9]{8}|[0-9]{4}-[0-9]{2}-[0-9]{2})T[0-9]{6}Z$",
    ),
    AfterValidator(_validate_corpus_version),
]


class StrictContractModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=True,
    )


def _json_array_to_tuple(value: object) -> tuple[object, ...]:
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    raise ValueError("value must be a JSON array")


class LocalEvidenceProbeRequestV1(StrictContractModel):
    request_id: StableId
    source_id: StableId
    audit_id: StableId
    claim_id: StableId
    query: Annotated[str, StringConstraints(strict=True, min_length=1, max_length=4000)]
    kb_book_id: Annotated[str, StringConstraints(strict=True, min_length=1, max_length=256)]
    query_mode: Literal["evidence"]
    top_k: Annotated[int, Field(strict=True, ge=1, le=20)]


class LocalEvidenceQueryPlanV1(StrictContractModel):
    schema_version: Literal["local-evidence-query-plan/v1"]
    plan_id: StableId
    policy_version: Literal["vfl-readonly-probe/1.0.0"]
    source_id: StableId
    audit_id: StableId
    execution_scope: Literal["hermetic_test", "reviewed_live"]
    collection: Annotated[str, StringConstraints(strict=True, min_length=1, max_length=256)]
    kb_book_id: Annotated[str, StringConstraints(strict=True, min_length=1, max_length=256)]
    expected_corpus_version: CorpusVersion
    requests: Annotated[
        tuple[LocalEvidenceProbeRequestV1, ...],
        BeforeValidator(_json_array_to_tuple),
    ]

    @model_validator(mode="after")
    def validate_plan(self) -> Self:
        if not self.requests:
            raise ValueError("requests must not be empty")
        request_ids = tuple(item.request_id for item in self.requests)
        claim_ids = tuple(item.claim_id for item in self.requests)
        if len(set(request_ids)) != len(request_ids):
            raise ValueError("request IDs must be unique")
        if len(set(claim_ids)) != len(claim_ids):
            raise ValueError("claim IDs must be unique")
        if claim_ids != tuple(sorted(claim_ids)):
            raise ValueError("requests must use canonical claim order")
        if any(
            item.source_id != self.source_id
            or item.audit_id != self.audit_id
            or item.kb_book_id != self.kb_book_id
            for item in self.requests
        ):
            raise ValueError("request identities must match the plan")
        if self.collection != "local_kb_kaiyuan_v2" and not re.fullmatch(
            r"test_vfl_ephemeral_[a-z0-9_]+", self.collection
        ):
            raise ValueError("collection is not allowed")
        if (
            self.execution_scope == "reviewed_live"
            and self.collection != "local_kb_kaiyuan_v2"
        ) or (
            self.execution_scope == "hermetic_test"
            and not re.fullmatch(r"test_vfl_ephemeral_[a-z0-9_]+", self.collection)
        ):
            raise ValueError("execution scope and collection do not agree")
        return self


class LocalKBSourceFileV1(StrictContractModel):
    relative_path: Annotated[str, StringConstraints(strict=True, min_length=1, max_length=4096)]
    size_bytes: Annotated[int, Field(strict=True, ge=0, le=64 * 1024 * 1024)]
    sha256: Sha256Hex

    @model_validator(mode="after")
    def validate_relative_path(self) -> Self:
        value = self.relative_path
        path = PurePosixPath(value)
        if (
            value.startswith("/")
            or "\\" in value
            or "//" in value
            or path.as_posix() != value
            or any(part in {"", ".", ".."} for part in path.parts)
            or path.suffix != ".md"
        ):
            raise ValueError("source path is not canonical")
        normalized = f"/{value}"
        if (
            "/分卷/" not in normalized
            and "全文合併版" not in normalized
            and "全文合并版" not in normalized
        ):
            raise ValueError("source path is not scanner-eligible")
        return self


class LocalKBSourceSnapshotV1(StrictContractModel):
    schema_version: Literal["local-kb-source-snapshot/v1"]
    snapshot_id: StableId
    corpus_version: CorpusVersion
    collection: Annotated[str, StringConstraints(strict=True, min_length=1, max_length=256)]
    kb_book_id: Annotated[str, StringConstraints(strict=True, min_length=1, max_length=256)]
    files: Annotated[
        tuple[LocalKBSourceFileV1, ...],
        BeforeValidator(_json_array_to_tuple),
    ]
    tree_sha256: Sha256Hex

    @model_validator(mode="after")
    def validate_snapshot(self) -> Self:
        paths = tuple(item.relative_path for item in self.files)
        if paths != tuple(sorted(paths)) or len(set(paths)) != len(paths):
            raise ValueError("snapshot files must be sorted and unique")
        payload = [item.model_dump(mode="json") for item in self.files]
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        if hashlib.sha256(canonical).hexdigest() != self.tree_sha256:
            raise ValueError("snapshot tree hash does not match")
        return self


@dataclass(frozen=True, slots=True)
class SourceSnapshotBindingV1:
    canonical_kb_root: Path
    snapshot_sha256: str
    collection: str
    kb_book_id: str
    corpus_version: str


class ReadOnlyTwoStageRetriever(Protocol):
    @property
    def source_binding(self) -> SourceSnapshotBindingV1:
        ...

    def two_stage_retrieve(
        self, query: str, **kwargs: object
    ) -> Mapping[str, object]:
        raise NotImplementedError
```

Tests must reject unknown fields, duplicate request or claim IDs, blank
queries, `top_k` outside `1..20`, duplicate snapshot paths, absolute or
non-normalized paths, malformed hashes, non-`fenjuan|fulltext` paths, snapshot
collection/corpus/book disagreement with the plan, a plan whose requests do not
exactly cover the audit claims, mixed identities and any production collection
other than `local_kb_kaiyuan_v2`. Reject an unknown `execution_scope`, either
crossed scope/collection pair and a hermetic plan passed to the production
binder. A separate test-only
constructor may accept `test_vfl_ephemeral_*` only when passed a recording fake;
there is no public boolean bypass.

Add coercion adversaries: booleans for integer fields, numeric strings for
sizes/`top_k`, integers for IDs/queries/hashes and whitespace-only strings all
fail instead of being converted by Pydantic.

Use the shared `CorpusVersion` for plan and snapshot. Accept exact valid dates
in the two producer forms `YYYYMMDDTHHMMSSZ` and
`YYYY-MM-DDTHHMMSSZ`; reject invalid calendar/time values, control or whitespace
characters, `=`, slash/backslash, descriptive suffixes and all other forms.
Task 3 applies the same validator to upstream meta. The pre-validator runs
before model-level `str_strip_whitespace` can normalize an unsafe caller value.

Add happy-path tests that pass ordinary JSON-decoded `list` values for both
`requests` and `files` through `load_query_plan_v1()` and
`load_source_snapshot_v1()`, respectively, and assert the frozen model stores
tuples. The narrow `BeforeValidator` above is required because strict Pydantic
tuple fields otherwise reject JSON-decoded lists; duplicate-aware `json.loads`
must remain the only JSON parser and must not be replaced by
`model_validate_json()`.

Call `bind_source_snapshot_to_plan()` before any retriever or accessor
construction and test all three exact equalities: collection, `kb_book_id` and
corpus version.

Run RED:

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)/apps/star-omen"
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
  ../../.venv/bin/python -m pytest -q \
  tests/video_pipeline/feedback_loop/test_readonly_contracts_v1.py
```

Expected: import failure because `readonly_contracts_v1` does not exist.

- [ ] **Step 2: Implement closed models and plan/audit binding**

Implement canonical identity bytes with the repository's existing canonical
JSON helper. Define one safe exception boundary used throughout S1:

```python
class ReadOnlyErrorCode(StrEnum):
    INVALID_LOCAL_INPUT = "invalid_local_input"
    RIGHTS_REJECTED = "rights_rejected"
    PLAN_MISMATCH = "plan_mismatch"
    SNAPSHOT_MISMATCH = "snapshot_mismatch"
    ENDPOINT_REJECTED = "endpoint_rejected"
    CREDENTIAL_UNAVAILABLE = "credential_unavailable"
    TRANSPORT_FAILED = "transport_failed"
    RESPONSE_CONTRACT_REJECTED = "response_contract_rejected"
    EVIDENCE_PROJECTION_REJECTED = "evidence_projection_rejected"
    SOURCE_INTEGRITY_FAILED = "source_integrity_failed"
    OUTPUT_CONFLICT = "output_conflict"


class ReadOnlyAdapterError(RuntimeError):
    code: ReadOnlyErrorCode
    failed_claim_id: str | None

    def __init__(
        self,
        code: ReadOnlyErrorCode,
        *,
        failed_claim_id: str | None = None,
    ) -> None:
        self.code = code
        self.failed_claim_id = failed_claim_id
        super().__init__(code.value)
```

Its message is fixed from the enum and never contains a wrapped exception,
path, URL, credential, payload or source text. CLI code later maps all expected
Pydantic, OS, KB and package failures into this allowlist using a concrete form
such as `raise ReadOnlyAdapterError(ReadOnlyErrorCode.TRANSPORT_FAILED) from
None`.

Expose only narrow internal binding helpers:

```python
def bind_production_query_plan_to_audit(
    *,
    plan: LocalEvidenceQueryPlanV1,
    audit_bundle: ExternalAuditBundleV1,
) -> None:
    if (
        plan.execution_scope != "reviewed_live"
        or plan.collection != "local_kb_kaiyuan_v2"
    ):
        raise ReadOnlyAdapterError(ReadOnlyErrorCode.PLAN_MISMATCH)
    if plan.source_id != audit_bundle.source.source_id:
        raise ReadOnlyAdapterError(ReadOnlyErrorCode.PLAN_MISMATCH)
    if plan.audit_id != audit_bundle.audit.audit_id:
        raise ReadOnlyAdapterError(ReadOnlyErrorCode.PLAN_MISMATCH)
    claim_ids = tuple(sorted(claim.claim_id for claim in audit_bundle.claims))
    if tuple(request.claim_id for request in plan.requests) != claim_ids:
        raise ReadOnlyAdapterError(ReadOnlyErrorCode.PLAN_MISMATCH)


def bind_source_snapshot_to_plan(
    *,
    snapshot: LocalKBSourceSnapshotV1,
    plan: LocalEvidenceQueryPlanV1,
) -> None:
    if (
        snapshot.collection != plan.collection
        or snapshot.kb_book_id != plan.kb_book_id
        or snapshot.corpus_version != plan.expected_corpus_version
    ):
        raise ReadOnlyAdapterError(ReadOnlyErrorCode.SNAPSHOT_MISMATCH)


def canonical_contract_sha256(model: BaseModel) -> str:
    return hashlib.sha256(canonical_contract_bytes(model)).hexdigest()
```

The contract permits only `local_kb_kaiyuan_v2` or the
`test_vfl_ephemeral_*` namespace and enforces the exact scope/collection pairs
`reviewed_live`/`local_kb_kaiyuan_v2` and
`hermetic_test`/`test_vfl_ephemeral_*`. The production binding above accepts
only the former. Hermetic adapter/E2E tests use a private test-owned dependency
constructor that requires the concrete recording-fake type and the latter pair;
production code exposes no boolean, duck-typed or CLI bypass for it. A public
CLI test passes the committed hermetic fixture and proves rejection before
credential, transport or retrieval access.

- [ ] **Step 3: Write failing strict-file tests**

Tests must cover:

- `O_NOFOLLOW` single-path open and rejection of symlinks/non-regular files;
- FIFO/device/socket inputs rejected without blocking;
- audit `2 MiB`, plan/snapshot `256 KiB` bounded reads;
- two reads from the same descriptor with before/between/after `fstat` checks;
- replacement, truncation, in-place rewrite and unequal-read detection;
- strict UTF-8, duplicate JSON keys and `NaN`/`Infinity` rejection;
- JSON decoder `RecursionError`, nesting deeper than 64 and more than 100,000
  mapping/list/scalar nodes rejected with the same fixed typed error for each
  audit/plan/snapshot loader;
- audit rights allowlist (`metadata_only`, `quotation_for_research`,
  `permission_confirmed`, `public_domain`) and exact `research_only=true`,
  `grants_rule_authority=false`, `grants_classical_authority=false` flags;
- unreferenced capture with `rights_status="unknown"` rejecting the batch;
- typed fixed error codes whose rendered messages contain no path or payload.

Run RED:

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)/apps/star-omen"
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
  ../../.venv/bin/python -m pytest -q \
  tests/video_pipeline/feedback_loop/test_readonly_inputs_v1.py
```

Expected: import failure because `strict_local_files` does not exist.

- [ ] **Step 4: Implement the strict loader**

Use `os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW |
os.O_NONBLOCK)` (plus `O_NOCTTY` when available), immediately require
`stat.S_ISREG(os.fstat(fd).st_mode)`, then perform bounded reads, strict UTF-8
and a duplicate-detecting `object_pairs_hook`. Parse constants must raise
instead of accepting non-finite numbers. The post-decode graph walk also
rejects every float for which `math.isfinite()` is false, including overflow
spellings `1e999` and `-1e999` that bypass `parse_constant`. Catch decoder
`RecursionError`, then walk the decoded graph iteratively before Pydantic with
maximum depth 64 and maximum 100,000 total mapping/list/scalar nodes; budget,
decoder and model errors all become `INVALID_LOCAL_INPUT` from no retained
cause. Return immutable bytes plus the parsed model; never reopen the path.

```python
@dataclass(frozen=True)
class StrictJSONDocument(Generic[T]):
    raw_bytes: bytes
    raw_sha256: str
    canonical_sha256: str
    value: T


def load_external_audit_v1(path: Path) -> StrictJSONDocument[ExternalAuditBundleV1]:
    return _load_strict_json(path, max_bytes=2 * 1024 * 1024, model=ExternalAuditBundleV1)


def load_query_plan_v1(path: Path) -> StrictJSONDocument[LocalEvidenceQueryPlanV1]:
    return _load_strict_json(path, max_bytes=256 * 1024, model=LocalEvidenceQueryPlanV1)


def load_source_snapshot_v1(path: Path) -> StrictJSONDocument[LocalKBSourceSnapshotV1]:
    return _load_strict_json(path, max_bytes=256 * 1024, model=LocalKBSourceSnapshotV1)
```

`_load_strict_json()` owns the exact open/fstat/double-read/strict-decode/model
validation sequence described above and computes raw and canonical SHA-256
values from the two already-frozen byte/model forms.

- [ ] **Step 5: Verify and deliver Task 1**

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)/apps/star-omen"
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
  ../../.venv/bin/python -m pytest -q \
  tests/video_pipeline/feedback_loop/test_readonly_contracts_v1.py \
  tests/video_pipeline/feedback_loop/test_readonly_inputs_v1.py
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
  ../../.venv/bin/python -m pytest -q tests/video_pipeline/feedback_loop
cd "$(git rev-parse --show-toplevel)"
git diff --check
git status --short
git add apps/star-omen/src/video_pipeline/feedback_loop/readonly_contracts_v1.py \
  apps/star-omen/src/video_pipeline/feedback_loop/strict_local_files.py \
  apps/star-omen/tests/video_pipeline/feedback_loop/test_readonly_contracts_v1.py \
  apps/star-omen/tests/video_pipeline/feedback_loop/test_readonly_inputs_v1.py
test "$(git symbolic-ref --short HEAD)" = codex/kaiyuan-feedback-loop-readonly-adapters-v1
git diff --cached --check
test "$(git diff --cached --name-only)" = "$(printf '%s\n' \
  apps/star-omen/src/video_pipeline/feedback_loop/readonly_contracts_v1.py \
  apps/star-omen/src/video_pipeline/feedback_loop/strict_local_files.py \
  apps/star-omen/tests/video_pipeline/feedback_loop/test_readonly_contracts_v1.py \
  apps/star-omen/tests/video_pipeline/feedback_loop/test_readonly_inputs_v1.py)"
git commit -m "feat: add strict feedback loop readonly inputs"
S1_STATUS=$(git status --porcelain)
test -z "$S1_STATUS"
```

Non-force push the S1 branch and verify fetched remote tree equals local
`HEAD^{tree}` before Task 2.

---

### Task 2: Pin local source bytes and add scanner/resolver loader seams

**Files:**

- Create:
  `apps/star-omen/src/video_pipeline/feedback_loop/source_snapshot_v1.py`
- Create:
  `apps/star-omen/tests/video_pipeline/feedback_loop/test_source_snapshot_v1.py`
- Modify: `apps/star-omen/src/connectors/primary_passage_cache.py`
- Modify: `apps/star-omen/src/connectors/primary_file_scanner.py`
- Modify: `apps/star-omen/src/connectors/evidence_resolver.py`
- Modify: `apps/star-omen/tests/test_primary_passage_cache_v2.py`
- Modify: `apps/star-omen/tests/test_kaiyuan_retrieval_v2.py`
- Modify: `apps/star-omen/tests/test_evidence_resolver.py`
- Modify: `apps/star-omen/tests/test_citable_evidence_v2.py`

**Interfaces:**

- Consumes: Task 1's `LocalKBSourceSnapshotV1`, `SourceSnapshotBindingV1` and
  `ReadOnlyAdapterError`, plus
  existing `PrimarySourceSnapshot`, scanner and resolver APIs.
- Produces: `PrimarySourceByteLoader.load(path, *, card_type, kb_book_id,
  book_title) -> PrimarySourceSnapshot`,
  `PrimarySourceByteLoader.relative_paths() -> tuple[str, ...]`,
  `build_primary_source_snapshot(raw_bytes, *, path, mtime_ns, card_type,
  kb_book_id, book_title) -> PrimarySourceSnapshot`,
  `LocalKBSourceAccessor.open(*, kb_root, snapshot)`, and optional keyword-only
  `passage_loader` / `strict_exact_passages` seams on scanner and resolver,
  plus the narrow immutable `EvidenceResolverContext` seam.

- [ ] **Step 1: Write failing snapshot-accessor tests**

Create temporary roots with regular, symlinked and nested files. Assert exact
eligible inventory (`fenjuan` and `fulltext` only), per-file `64 MiB`, total
`512 MiB`, sorted manifest paths, file hashes and canonical tree hash. Assert
that missing/extra/replaced/restored/in-place-mutated files, symlinked path
components, FIFO/device/socket terminal entries and wrong `kb_book_id` fail
without blocking and with typed safe errors. The accessor
must hold a root descriptor and read beneath it component by component without
following symlinks.

Run RED:

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)/apps/star-omen"
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
  ../../.venv/bin/python -m pytest -q \
  tests/video_pipeline/feedback_loop/test_source_snapshot_v1.py
```

- [ ] **Step 2: Implement the root-fd accessor**

```text
LocalKBSourceAccessor.open(
    *, kb_root: Path, snapshot: LocalKBSourceSnapshotV1
) -> LocalKBSourceAccessor
LocalKBSourceAccessor.binding -> SourceSnapshotBindingV1
LocalKBSourceAccessor.assert_bound(
    *, kb_root: Path, snapshot: LocalKBSourceSnapshotV1,
    snapshot_sha256: str
) -> None
LocalKBSourceAccessor.load(
    path: str | Path,
    *, card_type: str, kb_book_id: str, book_title: str
) -> PrimarySourceSnapshot
LocalKBSourceAccessor.relative_paths() -> tuple[str, ...]
LocalKBSourceAccessor.assert_unchanged() -> None
LocalKBSourceAccessor.close() -> None
LocalKBSourceAccessor.__enter__() -> LocalKBSourceAccessor
LocalKBSourceAccessor.__exit__(*args: object) -> None
```

Open every relative component with `dir_fd` and `O_NOFOLLOW`; intermediate
components use `O_DIRECTORY`, and the final component also uses `O_NONBLOCK`
before an immediate regular-file `fstat` gate. Reject platforms without
equivalent support. `load()` reads and verifies immutable bytes from
that descriptor and parses them through `build_primary_source_snapshot()`;
scanner and resolver receive the resulting snapshot and never reopen a path.
Do not cache by pathname. `relative_paths()` returns exactly the snapshot's
already-validated sorted file tuple; it does not enumerate the live tree.
Preflight and postflight independently recompute live inventory, sizes, hashes
and tree identity through the root descriptor.
The accessor stores one immutable binding established at `open()`.
`assert_bound()` requires exact root identity, snapshot semantic identity and
caller canonical snapshot SHA-256 before any source load. Tests cover root and
snapshot mismatch.

- [ ] **Step 3: Write failing additive-seam tests**

Specify one narrow loader protocol and a pure bytes builder:

```text
PrimarySourceByteLoader.load(
    path: str | Path,
    *, card_type: str, kb_book_id: str, book_title: str
) -> PrimarySourceSnapshot
PrimarySourceByteLoader.relative_paths() -> tuple[str, ...]
build_primary_source_snapshot(
    raw_bytes: bytes,
    *,
    path: Path,
    mtime_ns: int,
    card_type: str,
    kb_book_id: str,
    book_title: str,
) -> PrimarySourceSnapshot
```

Require a strict non-boolean integer `mtime_ns`; the returned existing
`PrimarySourceSnapshot.mtime_ns` stays an `int`. The accessor passes the final
descriptor's `fstat().st_mtime_ns`; tests use explicit integers. No dataclass
field or legacy cache contract is widened to `None`.

Tests inject a counting loader into scanner and resolver and replace the global
path cache with a fail-fast spy. Assert one verified byte source feeds both,
snapshot integrity errors propagate instead of becoming empty/missing hits,
and legacy calls without a loader preserve existing behavior. In strict mode,
the scanner must iterate only `passage_loader.relative_paths()` in its supplied
canonical order and must never call `Path.rglob()` or enumerate the live root.
Remove a manifest file only for the duration of its scanner turn and restore it
before postflight; the exact manifest-path load must still abort rather than
silently omit the file under the same identity. Add a candidate
whose original relative path contains a symlinked intermediate component;
assert the injected resolver branch does not call `Path.resolve()`, passes the
original lexically validated relative path to the accessor and aborts on the
accessor's no-follow check.

The existing resolver currently reads `get_settings()` unconditionally even
when `kb_root` is explicit. Add:

```text
EvidenceResolverContext(
    source_root_label: str,
    ingest_source_label: str,
)
```

and an optional keyword-only `resolver_context` seam. When both explicit
`kb_root` and `resolver_context` are supplied, the resolver must not call
`get_settings()` or consult `APP_CONFIG_PATH`; it uses only that context for
the two legacy label defaults. The legacy call path constructs the same
context from `get_settings()` and remains unchanged. Tests install a fail-fast
`get_settings` spy, change to an unrelated CWD and prove the injected branch
still resolves from the snapshot loader only.

For a scanner exact match, locate the unique parsed passage satisfying
`passage.raw_start <= match.start` and `match.end <= passage.raw_end`; emit that
passage's page/heading/paragraph, `raw_content_hash` and
`normalized_content_hash`. Never substitute the whole-file hash or the
scanner cluster paragraph index.

Run the new seam tests RED before implementation:

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)/apps/star-omen"
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
  ../../.venv/bin/python -m pytest -q \
  tests/test_primary_passage_cache_v2.py \
  tests/test_kaiyuan_retrieval_v2.py \
  tests/test_evidence_resolver.py \
  tests/test_citable_evidence_v2.py
```

Expected: the new tests fail because the loader parameters, pure byte parser
and strict passage projection do not exist.

- [ ] **Step 4: Implement the additive seams**

Keep every new parameter keyword-only and optional:

```text
scan_primary_files(
    settings: Settings,
    query: str,
    *,
    book_id: str | None,
    mode: str,
    limit: int,
    query_variants: Sequence[str],
    passage_loader: PrimarySourceByteLoader | None = None,
    strict_exact_passages: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]


resolve_evidence(
    evidence: dict[str, Any],
    kb_root: str | Path | None = None,
    *,
    passage_loader: PrimarySourceByteLoader | None = None,
    resolver_context: EvidenceResolverContext | None = None,
) -> dict[str, Any]
```

Default `None` paths continue using the existing cache and error mapping. The
S1 loader path neither calls `Path.resolve()`/`Path.is_file()` on a child nor
reopens a path; it performs only lexical canonical/confinement validation and
lets the accessor enforce each component. The strict S1 scanner requires the
loader inventory, iterates those exact manifest paths instead of live `rglob`,
and does not catch typed integrity errors. The resolver's explicit
root/context/loader branch never loads global settings. Its typed integrity
exceptions are not swallowed.

- [ ] **Step 5: Verify and deliver Task 2**

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)/apps/star-omen"
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
  ../../.venv/bin/python -m pytest -q \
  tests/video_pipeline/feedback_loop/test_source_snapshot_v1.py \
  tests/test_primary_passage_cache_v2.py \
  tests/test_kaiyuan_retrieval_v2.py \
  tests/test_evidence_resolver.py \
  tests/test_citable_evidence_v2.py
cd "$(git rev-parse --show-toplevel)"
git diff --check
git add apps/star-omen/src/connectors/primary_passage_cache.py \
  apps/star-omen/src/connectors/primary_file_scanner.py \
  apps/star-omen/src/connectors/evidence_resolver.py \
  apps/star-omen/src/video_pipeline/feedback_loop/source_snapshot_v1.py \
  apps/star-omen/tests/test_primary_passage_cache_v2.py \
  apps/star-omen/tests/test_kaiyuan_retrieval_v2.py \
  apps/star-omen/tests/test_evidence_resolver.py \
  apps/star-omen/tests/test_citable_evidence_v2.py \
  apps/star-omen/tests/video_pipeline/feedback_loop/test_source_snapshot_v1.py
test "$(git symbolic-ref --short HEAD)" = codex/kaiyuan-feedback-loop-readonly-adapters-v1
git diff --cached --check
test "$(git diff --cached --name-only)" = "$(printf '%s\n' \
  apps/star-omen/src/connectors/evidence_resolver.py \
  apps/star-omen/src/connectors/primary_file_scanner.py \
  apps/star-omen/src/connectors/primary_passage_cache.py \
  apps/star-omen/src/video_pipeline/feedback_loop/source_snapshot_v1.py \
  apps/star-omen/tests/test_citable_evidence_v2.py \
  apps/star-omen/tests/test_evidence_resolver.py \
  apps/star-omen/tests/test_kaiyuan_retrieval_v2.py \
  apps/star-omen/tests/test_primary_passage_cache_v2.py \
  apps/star-omen/tests/video_pipeline/feedback_loop/test_source_snapshot_v1.py)"
git commit -m "feat: pin feedback loop source snapshots"
S1_STATUS=$(git status --porcelain)
test -z "$S1_STATUS"
```

Push/read back the exact remote tree before Task 3.

---

### Task 3: Add literal-loopback transport and a strict pre-fallback seam

**Files:**

- Create:
  `apps/star-omen/src/video_pipeline/feedback_loop/readonly_kb_v1.py`
- Create:
  `apps/star-omen/tests/video_pipeline/feedback_loop/test_readonly_kb_v1.py`
- Create: `apps/star-omen/tests/test_transport_security_v2.py`
- Modify: `apps/star-omen/src/config/settings.py`
- Modify: `apps/star-omen/src/config/__init__.py`
- Modify: `apps/star-omen/src/connectors/kb_retrieval/transport.py`
- Modify: `apps/star-omen/src/connectors/kb_retrieval/client.py`
- Modify: `apps/star-omen/src/connectors/kb_retrieval/core.py`
- Modify: `apps/star-omen/src/connectors/kb_retrieval/two_stage.py`
- Modify: `apps/star-omen/tests/test_config.py`
- Modify: `apps/star-omen/tests/test_retriever.py`
- Modify: `apps/star-omen/tests/test_official_two_stage_v2.py`
- Modify: `apps/star-omen/tests/test_transport_error_taxonomy_v2.py`

**Interfaces:**

- Consumes: Task 1's error/contracts and Task 2's
  `PrimarySourceByteLoader` / `EvidenceResolverContext`; existing `Settings`, `TransportMixin`,
  `KBSearchRetriever.retrieve()` and `two_stage_retrieve()`.
- Produces: `resolve_kb_search_config_path(config_path: Path | None) -> Path`,
  `load_kb_search_endpoint(config_path: Path) -> str`,
  `validate_literal_loopback_endpoint(value: str) -> str`,
  `JSONRequestTransport`, `PinnedHTTPXJSONTransport`,
  `VerifiedUpstreamProvenanceV1`, `PinnedReadOnlyKBSession`,
  `RawRetrieveResponseValidator`, `validate_upstream_meta(response, *,
  collection, expected_corpus_version)`,
  `validate_raw_official_retrieve_response(response, *, request_payload,
  verified_provenance) -> None`, and
  `build_readonly_kb_retriever(*, kb_root, collection,
  expected_corpus_version, source_byte_loader, config_path=None) ->
  PinnedReadOnlyKBSession`.

- [ ] **Step 1: Write failing endpoint/config tests**

Add an endpoint-only loader that never touches API-key interpolation:

```text
resolve_kb_search_config_path(config_path: Path | None = None) -> Path
load_kb_search_endpoint(config_path: Path) -> str
```

Test normal base-url/env/port precedence, unsupported endpoint interpolation
failure, and a credential trap proving invalid endpoint validation occurs
before any `KB_SEARCH_API_KEY` lookup, settings construction, transport
construction or network call.

Configuration resolution is exact and performed once: explicit internal path,
else non-empty `APP_CONFIG_PATH`, else
`Path(__file__).resolve().parents[2] / "config/config.yaml"` inside
`src/config/settings.py`. Resolve
the selected path to an absolute path, require a regular file and pass that same
object to both endpoint-only parsing and later `load_settings`. Tests change CWD
to repository root and an unrelated temporary directory, clear
`APP_CONFIG_PATH`, and prove the module-derived default remains identical; they
also prove one explicit/env path is reused without a second resolution.

`validate_literal_loopback_endpoint()` accepts only `http://127.0.0.1:PORT`
and `http://[::1]:PORT`, with port `1..65535` and path empty or `/`. Reject
whitespace/control characters, HTTPS, userinfo, query, fragment, hostname
`localhost`, `127.1`, integer/octal IPv4, expanded alternative IPv6 spelling,
IPv4-mapped/scoped IPv6, missing/zero/out-of-range ports and any remote host.
Errors do not echo the URL.

- [ ] **Step 2: Write failing strict-transport tests**

Define the injected protocol and implementation:

```text
JSONRequestTransport.request(
    method: str,
    url: str,
    *, json_payload: dict[str, Any] | None,
    headers: dict[str, str],
    timeout: float,
) -> dict[str, Any]
PinnedHTTPXJSONTransport(validated_origin: str)
VerifiedUpstreamProvenanceV1(
    corpus_version: str,
    collection: str,
    ingest_run_id: str,
    source_manifest_hash: str,
    created_at: str,
    session_meta_sha256: str,
    provenance_sha256: str,
)
RawRetrieveResponseValidator(
    response: Mapping[str, object],
    *, request_payload: Mapping[str, object]
) -> None
validate_upstream_meta(
    response: Mapping[str, object],
    *, collection: str,
    expected_corpus_version: str,
) -> VerifiedUpstreamProvenanceV1
validate_raw_official_retrieve_response(
    response: Mapping[str, object],
    *,
    request_payload: Mapping[str, object],
    verified_provenance: VerifiedUpstreamProvenanceV1,
) -> None


build_readonly_kb_retriever(
    *,
    kb_root: Path,
    collection: str,
    expected_corpus_version: str,
    source_accessor: LocalKBSourceAccessor,
    source_snapshot: LocalKBSourceSnapshotV1,
    source_snapshot_sha256: str,
    config_path: Path | None = None,
) -> PinnedReadOnlyKBSession
```

`PinnedReadOnlyKBSession` exposes the accessor's immutable `source_binding`
and one immutable `resolver_context` created by
the factory from the isolated settings copy. It contains only the source-root
and ingest-source labels, never the API key, URL, raw configuration or mutable
settings object. The S1 runtime must pass this explicit context to the resolver
and may not reconstruct it through global settings.

Patch `httpx.Client` and assert `trust_env=False`,
`follow_redirects=False`, exact origin enforcement before headers are sent,
all 3xx rejected without a second request, and no urllib request fallback when
httpx is missing. Require the transport itself to stream and parse the raw body:
only JSON media types and absent/identity content encoding, 256 KiB decoded
maximum for `/v1/meta`, 4 MiB for `/v1/retrieve`, early excessive
`Content-Length` rejection, immediate stop on streamed overflow, strict UTF-8,
duplicate-key-aware `object_pairs_hook`, non-finite constant rejection plus a
post-decode `math.isfinite()` walk rejecting `1e999` and `-1e999`, the
same depth-64/node-100,000 graph budget and a root mapping. Raw-body tests cover
invalid UTF-8, duplicate `collection`/`hits`, `NaN`/`Infinity`, excessive
declared and streamed bodies, wrong content type/encoding, over-depth/over-node
JSON and prove that `response.json()` is never called. Typed errors have fixed
messages, empty safe details and no exception cause containing key, URL,
response body or source text.

Run RED:

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)/apps/star-omen"
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
  ../../.venv/bin/python -m pytest -q \
  tests/test_config.py \
  tests/test_transport_security_v2.py \
  tests/video_pipeline/feedback_loop/test_readonly_kb_v1.py
```

- [ ] **Step 3: Implement safe transport and factory ordering**

`TransportMixin` accepts an optional injected `request_transport`; its legacy
branch stays unchanged. `KBSearchRetriever.__init__` preserves the original
five positional parameters and adds only keyword-only seams:

```text
KBSearchRetriever.__init__(
    self,
    base_url: str | None = None,
    api_key: str | None = None,
    timeout: float | None = None,
    default_collection: str | None = None,
    settings: Settings | None = None,
    *,
    request_transport: JSONRequestTransport | None = None,
    primary_source_byte_loader: PrimarySourceByteLoader | None = None,
    raw_response_validator: RawRetrieveResponseValidator | None = None,
    strict_primary_passages: bool = False,
    verified_upstream_provenance: VerifiedUpstreamProvenanceV1 | None = None,
    upstream_provenance_guard: Callable[[], None] | None = None,
) -> None
```

The S1 factory order is fixed: require collection to equal exactly
`local_kb_kaiyuan_v2` (rejecting `local_kb_default`, ephemeral and every other
name before configuration, transport, meta or credential access); recompute
the canonical snapshot SHA-256, require it to equal the caller value, and call
`source_accessor.assert_bound(...)` before any source load or retrieval; resolve the
config path once; load endpoint only from that path; validate literal loopback;
validate expected corpus/root/loader/httpx; construct the pinned
transport; GET `/v1/meta` without authentication; validate the exact deployed
`corpus-manifest/v1` fields and bind collection/corpus; only then load a fresh
uncached Settings from the same resolved path and require the credential; create an isolated
`dataclasses.replace` settings copy pinned to the validated origin, caller KB
root and plan collection with Obsidian and candidate overlay disabled; construct
the retriever with explicit key, pinned transport, snapshot accessor, strict raw
validator and verified provenance; derive the narrow resolver context from that
same isolated copy; wrap both in `PinnedReadOnlyKBSession`. Do not mutate global
Settings or expose base URL/API key in the CLI. Tests call the factory directly
with the default, an ephemeral name and another production-looking name and
require rejection before config-path, transport, meta, credential and retriever
spies; the test-owned hermetic fake path never calls this production factory.
The isolated settings copy also hard-pins
`kb_search_query_normalize=True`, `kb_search_query_s2t=True` and
`kb_search_query_t2s=True`; these are S1 wire-query policy, not caller config.
Both meta and retrieve use the exact finite constant
`S1_REQUEST_TIMEOUT_SECONDS = 10.0`, never any configured timeout. Hostile
config/env values `false`, `nan`, `inf`, zero, negative and huge numbers cannot
alter query variants/fallback or produce an unbounded request; tests assert the
exact wire queries, fallback behavior and timeout arguments.

`PinnedHTTPXJSONTransport` permits only the validated origin plus exact
`/v1/meta` and `/v1/retrieve` paths with no query or fragment. The former is
only `GET` with `json_payload=None` and no auth headers; the latter is only
`POST` with a mapping payload and the two explicit credential headers. Reject
method/path/payload/header mismatch before opening a client. It uses
`httpx.Client.stream(...)` and enforces the path-specific decoded-byte budget
while iterating; no eager response-body helper or caller-supplied parsed mapping
bypasses the strict decoder.

`PinnedReadOnlyKBSession.two_stage_retrieve()` re-fetches `/v1/meta` immediately
before and after delegating, validates it to a fresh immutable provenance value,
and requires exact canonical equality with the factory preflight. It returns no
partial envelope on drift. Recording fakes implement this narrow session
protocol without exposing a production bypass.

The same exact-meta comparison is injected into retrieval core as an optional
keyword-only `upstream_provenance_guard`. The strict S1 path invokes it
immediately before each official `/v1/retrieve` and in `finally` immediately
afterward; legacy callers leave it `None`. Define the immutable provenance
record and guard protocol in `kb_retrieval/transport.py` so connector modules do
not import the higher-level video-pipeline factory and create a layering cycle.

The concrete validator's extra verified-provenance argument is closed over before
injection, so the callable still implements `RawRetrieveResponseValidator`:

```python
raw_validator = functools.partial(
    validate_raw_official_retrieve_response,
    verified_provenance=verified_provenance,
)
```

- [ ] **Step 4: Write failing pre-fallback response tests**

Add exact deployed-response compatibility cases: a valid `/v1/retrieve`
mapping with no `corpus_version` succeeds only when the separately validated
preflight meta matches collection/corpus; a supplied response corpus value must
match that provenance. Cover missing mandatory response keys, wrong
stage/schema/query mode/collection/filter/card pools/counts, non-finite or
wrongly typed hits, future response corpus conflict and stage disagreement. A
raw primary response may have `hits=[]`; if non-empty, every hit must explicitly
carry a non-null `card_type` in the requested primary card pool. Missing, null
or wrong primary card types fail in the raw validator before core filtering,
and each case keeps the scanner spy at zero. `official_primary_empty` is true
only for a validated raw empty list, never because filtering removed malformed
hits.
Both a stage-1 mismatch and a malformed empty stage-2 official response must
fail before the scanner spy is called. A valid empty official result may invoke
snapshot-backed lexical fallback; a malformed result may not.

Meta tests cover missing/unknown/typed fields, non-`ok` status, wrong schema,
collection/corpus mismatch, malformed manifest hash and canonical SHA drift.
Meta `corpus_version` is first validated by the same exact `CorpusVersion`
calendar/grammar validator as plan and snapshot, before equality comparison.
The exact current `load_corpus_meta()` success shape is accepted: in addition
to the public required fields, accept either the script-writer variant with
string-list `source_roots` plus `excluded_roots`, or the normal-ingest variant
with exact `managed_by="local-kb-unified/v2"`,
`collection_schema="passage-v2"` and a closed non-negative strict-integer
`run_stats` object containing exactly `desired`, `new`, `changed`, `unchanged`,
`stale`, `upserted`, `deleted`, `errors` and `elapsed_ms`. Also accept the base
public fields alone; reject mixed or partial variants. The complete accepted
object, including all `run_stats`, enters `session_meta_sha256` for in-memory
before/after drift detection only. A separate persisted `provenance_sha256`
hashes a canonical projection containing exactly the six stable base fields
(`schema_version`, `corpus_version`, `ingest_run_id`, `source_manifest_hash`,
`collection`, `created_at`) plus exact key `producer_variant`. Its value is
`base` with no extension fields, `corpus_manifest_script` with
`source_roots`/`excluded_roots`, or `normal_ingest` with
`managed_by`/`collection_schema`. It excludes `meta_status` and all
`run_stats`. Build test values through the real
`scripts/corpus_manifest.py::write_manifest` and
`index-jobs/ingest.py::write_corpus_manifest` producers (with side effects
confined to temporary paths), then feed their exact `/v1/meta` shapes to the S1
validator. The ingest script is not imported normally because its top level
requires optional `requests`, `dotenv` and `qdrant_client` dependencies and
loads `.env`. Load it under a fresh unique module name with
`importlib.util.spec_from_file_location` inside a test-only context that
snapshots and restores `sys.modules`, `sys.path` and `os.environ`, temporarily
prepends the exact `index-jobs` directory,
installs minimal non-network module stubs for those optional imports plus
`desired_items`/`incremental`, makes `load_dotenv` a recording no-op, and
provides the production constants `MANAGED_BY="local-kb-unified/v2"` and
`COLLECTION_SCHEMA="passage-v2"`. Execute the real
`write_corpus_manifest()` body with empty deterministic desired items and exact
closed stats into `tmp_path`; assert no request/client/reconciliation stub was
called and restore all interpreter/environment state in `finally`. For the
script writer, use the same fresh unique-module loader and full `sys.modules`,
`sys.path` and `os.environ` snapshot/restore discipline as the ingest producer;
additionally `monkeypatch.chdir(tmp_path)` before loading and restore it
afterward so it cannot scan repository source roots. Snapshot the temporary
tree before/after and require that each producer creates only its named output
file. No producer test may read `.env`, connect to Qdrant or perform a network
call.
Credential, retriever and scanner spies remain at zero on preflight failure.
Session tests mutate meta before and after the first and second query and prove
whole-batch abort; core-guard tests also mutate it between stage 1 and stage 2
and after a failed raw request. A compatibility test uses the exact field set emitted by the
repository's deployed `RetrieveResponse` model rather than a richer fake.
Tests also prove that changing only `run_stats`, including `elapsed_ms`, changes
the session digest and triggers in-session drift but leaves the persisted
provenance digest unchanged across fresh sessions; changing any semantic
projection field changes the persisted provenance digest. Task 4 binds that
digest into probe/run identity and owns those higher-level identity assertions.
Strict-normalization tests prove a snippet-only primary hit remains without an
anchor and that absent locator/heading/book/card/hash values are not synthesized;
the existing legacy normalization tests must remain unchanged and green.

Run RED:

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)/apps/star-omen"
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
  ../../.venv/bin/python -m pytest -q \
  tests/test_official_two_stage_v2.py \
  tests/video_pipeline/feedback_loop/test_readonly_kb_v1.py
```

Expected: the scanner spy is called for a malformed empty official response
because no raw validator seam exists.

- [ ] **Step 5: Enforce raw validation before fallback**

Add an optional `raw_response_validator` invoked immediately after each raw
official `/v1/retrieve` response and before core normalization supplies
defaults or two-stage code considers filesystem fallback. It validates the raw
official response against its exact request payload. It does not require a
`corpus_version` field absent from the deployed service; if a future response
supplies one, it must equal `VerifiedUpstreamProvenanceV1`. Only after raw
validation, the keyword-only provenance seam adds the verified corpus version,
semantic provenance SHA and `corpus_provenance="upstream_meta"` to internal stage and top-level
observability dictionaries. It never labels those values as raw-response
fields, and the session-meta SHA never leaves the pinned session. In S1,
malformed or provenance-conflicting responses raise and never
scan local files. Default callers receive current behavior.

In the same strict S1 path, core normalization preserves deployed hit fields
without synthesizing anchor, locator, heading, book/card identity or hashes
from `snippet`, title, path inference or nested compatibility metadata. In
particular it must not create `anchor_text` from `snippet`. Incomplete official
provenance therefore remains incomplete for Task 4 to reject or snapshot-
rehydrate. Legacy default callers retain their current compatibility behavior.
The complete composed two-stage envelope is validated separately in Task 4.

- [ ] **Step 6: Verify and deliver Task 3**

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)/apps/star-omen"
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
  ../../.venv/bin/python -m pytest -q \
  tests/test_config.py \
  tests/test_transport_security_v2.py \
  tests/video_pipeline/feedback_loop/test_readonly_kb_v1.py \
  tests/test_transport_error_taxonomy_v2.py \
  tests/test_retriever.py \
  tests/test_official_two_stage_v2.py \
  tests/test_kaiyuan_retrieval_v2.py
cd "$(git rev-parse --show-toplevel)"
git diff --check
git add apps/star-omen/src/config/settings.py apps/star-omen/src/config/__init__.py \
  apps/star-omen/src/connectors/kb_retrieval/transport.py \
  apps/star-omen/src/connectors/kb_retrieval/client.py \
  apps/star-omen/src/connectors/kb_retrieval/core.py \
  apps/star-omen/src/connectors/kb_retrieval/two_stage.py \
  apps/star-omen/src/video_pipeline/feedback_loop/readonly_kb_v1.py \
  apps/star-omen/tests/test_config.py \
  apps/star-omen/tests/test_transport_security_v2.py \
  apps/star-omen/tests/test_retriever.py \
  apps/star-omen/tests/test_official_two_stage_v2.py \
  apps/star-omen/tests/test_transport_error_taxonomy_v2.py \
  apps/star-omen/tests/video_pipeline/feedback_loop/test_readonly_kb_v1.py
test "$(git symbolic-ref --short HEAD)" = codex/kaiyuan-feedback-loop-readonly-adapters-v1
git diff --cached --check
test "$(git diff --cached --name-only)" = "$(printf '%s\n' \
  apps/star-omen/src/config/__init__.py \
  apps/star-omen/src/config/settings.py \
  apps/star-omen/src/connectors/kb_retrieval/client.py \
  apps/star-omen/src/connectors/kb_retrieval/core.py \
  apps/star-omen/src/connectors/kb_retrieval/transport.py \
  apps/star-omen/src/connectors/kb_retrieval/two_stage.py \
  apps/star-omen/src/video_pipeline/feedback_loop/readonly_kb_v1.py \
  apps/star-omen/tests/test_config.py \
  apps/star-omen/tests/test_official_two_stage_v2.py \
  apps/star-omen/tests/test_retriever.py \
  apps/star-omen/tests/test_transport_error_taxonomy_v2.py \
  apps/star-omen/tests/test_transport_security_v2.py \
  apps/star-omen/tests/video_pipeline/feedback_loop/test_readonly_kb_v1.py)"
git commit -m "feat: harden feedback loop readonly retrieval"
S1_STATUS=$(git status --porcelain)
test -z "$S1_STATUS"
```

Push/read back the exact remote tree before Task 4.

---

### Task 4: Validate responses and build deterministic context-only probes

**Files:**

- Create:
  `apps/star-omen/src/video_pipeline/feedback_loop/readonly_adapter_v1.py`
- Create:
  `apps/star-omen/src/video_pipeline/feedback_loop/readonly_runtime_v1.py`
- Create:
  `apps/star-omen/tests/video_pipeline/feedback_loop/test_readonly_adapter_v1.py`
- Create:
  `apps/star-omen/tests/video_pipeline/feedback_loop/test_readonly_runtime_v1.py`

**Interfaces:**

- Consumes: Task 1 contracts/errors, Task 2 accessor/loader and resolver seam,
  Task 3 pinned session/verified upstream provenance and existing S0
  `LocalEvidenceReferenceV1` / `LocalEvidenceProbeV1`.
- Produces: `ValidatedTwoStageResultV1`, `ProjectionResultV1`,
  `validate_two_stage_response(response, *, request, plan)`,
  `project_citable_references(*, validated, request, kb_root, passage_loader,
  resolver_context, resolver=resolve_evidence)`, and `build_local_evidence_probes(*,
  audit_bundle, query_plan, plan_sha256, retriever, kb_root, source_snapshot,
  source_snapshot_sha256, source_accessor, resolver_context,
  resolver=resolve_evidence)`.

- [ ] **Step 1: Write failing two-stage-envelope and hit-projection matrices**

For each stage and top-level result require every specified field and exact
type. Stage 1 is exactly `schema_version="kb-retrieve/v2"`,
`query_mode="evidence"`, `retrieval_stage="structured_recall"`. Stage 2 is
exactly `schema_version="kb-two-stage/v2"`, `query_mode="evidence"`,
`retrieval_stage="primary_evidence"`. Its nested `official_result` is exactly
`schema_version="kb-retrieve/v2"`, `query_mode="evidence"`,
`retrieval_stage="primary_evidence"` and repeats the requested collection,
`filters={"kb_book_id": request.kb_book_id}` and ordered primary card pool.
Stage 1 requires that same requested collection/filter. The existing stage-2
mapping does not own `collection` or `filters`; do not require or synthesize
them there. Collection/corpus provenance is instead exact in
stage-1 observability, nested-official observability and outer observability as
specified below. Require each layer's contract-owned hit arrays, counts and
latency/observability fields with exact types and consistent provenance.
Unknown fields are accepted only where the upstream public contract already
allows them; missing mandatory fields never gain defaults. Parameterize every
missing or wrong schema/mode/stage/collection/filter value at each individual
layer and require rejection.

Assert the exact card pools and their order: stage 1 is
`["zhusu_card", "term_card", "extract_card"]`; stage 2 and its nested
`official_result` are `["fenjuan", "fulltext"]`. Assert the top-level
observability object has `schema_version="kb-observability/v1"`,
`operation="two_stage_retrieve"` and `provenance_conflicts=[]`. Parameterized
adversaries cover every missing, reordered, added or substituted card/status
and every observability mismatch.

Require `stage1.observability`, `stage2.official_result.observability` and the
outer observability object to carry the same lowercase 64-hex
`upstream_provenance_sha256` and
`corpus_provenance="upstream_meta"`, with `corpus_version` equal to the plan.
Tests reject missing, response-native/unknown provenance labels, provenance-hash
disagreement across stages and any attempt to use an unverified corpus default.

Cover every bounded list (`hits`, `exact_hits`, `related_hits`,
`primary_candidates`, `candidate_overlay_hits`, `structured_fallbacks`), exact
hits belonging to the primary candidate set, empty candidate overlay, finite
JSON, official/fallback provenance agreement and the exact
`official_primary_empty=true` / `fallback_used=true` /
`fallback_reason="official_primary_empty"` fallback gate. A missing
`match_type` is legal only for the same official hit present in both the
official exact hits and primary candidates, compared by exact strict canonical
sorted-key JSON bytes, with official-primary used and no fallback. Never use
Python mapping/list equality or membership here because `True == 1` and
`1 == 1.0`; adversarial tests cover both pairs. Fallback hits must explicitly
declare `exact_raw` or `exact_normalized`.

The projector's exact alias allowlist is: path from
`relative_path|source_path|path`, locator from `source_locator|locator`, anchor
from `anchor_text|raw_text|quote|excerpt`, and hashes only from
`content_hash|raw_content_hash|normalized_content_hash`. Normalize each path
alias first: an absolute path must resolve strictly beneath resolved `kb_root`
and then become its canonical relative path; a relative path must already be
canonical/confined. Multiple path aliases agree when those canonical relative
paths are identical, not when their source strings are identical. Tests accept
the deployed-shape pair of absolute `path` plus `relative_path` naming the same
file and reject distinct targets, outside-root and symlink escapes. Multiple
non-empty locator aliases and, separately, anchor aliases must be strict string
values with identical content or the hit is rejected. The three hash fields
are not interchangeable aliases and need not equal one another: validate each
under its original meaning as lowercase `sha256:<64 hex>` and require at least
one. Pass them unchanged to the resolver: `raw_content_hash` must match the
passage raw hash, `normalized_content_hash` the passage normalized hash, and
`content_hash` may match either the exact in-memory anchor SHA-256 or the
passage raw hash. Tests cover both `content_hash` alternatives, including an
anchor hash different from the raw-passage hash, and a different valid
normalized hash. Apply the same rules after offset rehydration. `snippet` is never an anchor. Every other apparent compatibility alias is
ignored rather than promoted into resolver input.
An explicit exact-hit status is limited to `official`, `citable` or `primary`;
`stale`, `pending`, `ambiguous`, candidate-only and unknown values abort rather
than reach the resolver. Require a confined canonical path, matching book ID,
non-empty page marker, string-list heading path and non-negative paragraph
index when those optional fields are supplied.
Only resolver `status="citable"` emits a reference. Unknown status, integrity
failure or provenance disagreement fails the batch; ordinary non-citable
statuses increment only the exact allowlisted per-status rejection counts:
`candidate_only`, `source_outside_root`, `missing_source`, `book_mismatch`,
`card_type_mismatch`, `locator_mismatch`, `page_mismatch`,
`paragraph_mismatch`, `heading_mismatch`, `anchor_mismatch` and
`hash_mismatch`.

Apply this exact taxonomy and test every row:

| Class | Examples | Required action |
|---|---|---|
| Batch contract/integrity failure | Malformed raw/two-stage envelope, provenance mismatch, snapshot/accessor integrity exception, unknown or malformed resolver result, inconsistent `citable` fields, reference-ID collision | Raise the typed adapter error for the current claim; complete batch and output remain absent |
| Candidate-local projection omission | Missing/conflicting path/locator/anchor/hash aliases, invalid or ambiguous offset rehydration, other hit-local allowlist defect after envelope validation | Omit before resolver where applicable; no reference, no resolver-status count and no candidate diagnostic persisted |
| Known non-citable resolver result | Exactly one of the eleven resolver statuses listed above | Omit the reference and increment only that exact aggregate counter |

Tests prove candidate omissions do not hide envelope defects, known resolver
statuses do not abort unrelated candidates, and every batch-failure case maps
to `failed_claim_id=request.claim_id` with no partial tuple/package.

Build the persisted locator exactly as
`kaiyuan-passage:v1:<source>:<page>:p<paragraph>`. Encode source and page as
UTF-8 using RFC 3986 percent-encoding with only unreserved characters literal
and uppercase `%HH`; encode paragraph as canonical unsigned decimal with no
sign or leading zero except `0`. Assert the exact template and byte escaping,
not merely round-trip equivalence. An
absolute source path is accepted only after resolving it and proving that the
resolved path is beneath the resolved `kb_root`; only then may the projector
convert it to a canonical relative path. A relative path is resolved through
the snapshot-bound loader and must remain confined by the same rule. Tests
cover in-root absolute paths plus outside-root and symlink escapes.

Set `evidence_sha256` only by validating the resolver passage
`raw_content_hash` against `sha256:<64 lowercase hex>` and stripping that
literal `sha256:` prefix. Tests prove that the stored value is exactly the
remaining 64 lowercase hexadecimal characters and reject a bare hash, wrong
prefix, uppercase hex or any competing hit-level hash.

A resolver result with `status="citable"` must also supply its canonical
`source_locator`, a non-empty `page_marker`, a non-negative integer
`paragraph_index` and a string-only `heading_path`. The final locator, page,
paragraph, heading and raw hash are derived only from that validated resolver
passage, never copied from the candidate hit. Missing/wrongly typed fields or
any disagreement with the snapshot-parsed passage aborts the whole batch;
parameterized tests cover each field independently.

Every accepted reference has exactly `evidence_class="citable_passage"`,
`relationship="context_only"`, and a fixed content-free note stating that
semantic support/contradiction remains unreviewed. The literal is exactly
`Semantic support or contradiction remains unreviewed.` Tests assert exact note
and reject any source text, score, path or semantic verdict in it.

For an official deployed-shape hit that has no allowlisted anchor field, accept
rehydration only when both `raw_start` and `raw_end` are strict non-boolean
integers with `0 <= raw_start < raw_end`. Load the canonical path through the
snapshot accessor, require exactly one parsed passage whose boundaries equal
that pair, require every supplied page/paragraph/heading/locator/hash field to
match under the field-specific locator/hash rules above, and pass only the passage's exact in-memory raw text to the
resolver. A fallback scanner hit must already provide an allowlisted exact
anchor. A real-shape compatibility test starts from the deployed response's
`snippet`-only hit, proves successful offset rehydration, and proves the
snippet itself is never read as an anchor or persisted. Missing, partial,
boolean, out-of-range, non-boundary or ambiguous offsets reject the candidate.

Tests permute and duplicate identical hits to prove stable deduplication and
ordering, and inject one reference ID reused for distinct locator/hash tuples
to require a whole-batch collision failure.

Run RED:

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)/apps/star-omen"
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
  ../../.venv/bin/python -m pytest -q \
  tests/video_pipeline/feedback_loop/test_readonly_adapter_v1.py
```

Expected: import failure because the two-stage validator and projector do not
exist.

- [ ] **Step 2: Implement strict validation and projection**

```python
@dataclass(frozen=True, slots=True)
class CanonicalExactHitV1:
    canonical_bytes: bytes


@dataclass(frozen=True, slots=True)
class ValidatedTwoStageResultV1:
    observed_corpus_version: str
    upstream_provenance_sha256: str
    corpus_provenance: Literal["upstream_meta"]
    response_schema_versions: tuple[str, ...]
    exact_hits: tuple[CanonicalExactHitV1, ...]
    exact_candidate_count: int


@dataclass(frozen=True, slots=True)
class ProjectionResultV1:
    references: tuple[LocalEvidenceReferenceV1, ...]
    rejection_counts: tuple[tuple[str, int], ...]
```

After all envelope, provenance and hit-field checks succeed,
`validate_two_stage_response()` encodes each `stage2.exact_hits` mapping as
strict canonical JSON bytes (`ensure_ascii=False`, `allow_nan=False`, sorted
keys and compact separators), removes only byte-identical mappings, sorts the
remaining mappings by those bytes and stores immutable
`CanonicalExactHitV1(canonical_bytes=...)` wrappers in
`ValidatedTwoStageResultV1.exact_hits`. Set `exact_candidate_count` to exactly
`len(validated.exact_hits)`. Distinct hit mappings remain distinct candidates
even when projection later resolves them to the same passage; reference
deduplication is the separate projection rule below. Step 2 tests permute hits
and add an identical duplicate, then assert the immutable validated tuple and
exact candidate count are unchanged. Notes, probe ID and S0 run ID are
runtime-owned assertions in Steps 3–4. An alias-safety test mutates every
caller-owned response mapping after validation and proves the wrappers and
projection remain unchanged; projection decodes a fresh mapping from each
wrapper and never exposes a retained mutable alias.


Required function signatures:

```text
validate_two_stage_response(
    response: Mapping[str, object],
    *,
    request: LocalEvidenceProbeRequestV1,
    plan: LocalEvidenceQueryPlanV1,
) -> ValidatedTwoStageResultV1


project_citable_references(
    *,
    validated: ValidatedTwoStageResultV1,
    request: LocalEvidenceProbeRequestV1,
    kb_root: Path,
    passage_loader: PrimarySourceByteLoader,
    resolver_context: EvidenceResolverContext,
    resolver: Callable[..., Mapping[str, object]] = resolve_evidence,
) -> ProjectionResultV1
```

Deduplicate accepted passage candidates first by
`(request.claim_id, encoded_locator, evidence_sha256)`, derive the deterministic
reference ID as `evidence:vfl:s1:<sha256>`, where the digest is over canonical
sorted-key JSON with the exact keys `claim_id`, `evidence_locator` and
`evidence_sha256`. Reject one derived/reused ID mapping to
different locator/hash content, then sort final references by
`(encoded_locator, evidence_sha256, reference_id)`. Never reuse
rule-assessment's permissive `_hit_to_evidence()` helper. Define
`citable_count` as exactly `len(ProjectionResultV1.references)` after this
reference deduplication, never as the number of resolver calls or pre-dedup
`status="citable"` results. A test uses two distinct exact-hit mappings that
resolve to the same passage and asserts `exact_candidate_count=2`, one final
reference and `citable_count=1`.
Maintain one whole-batch reference-ID registry mapping every reference ID to
the complete `(claim_id, encoded_locator, evidence_sha256)` tuple. Any reuse
for a different tuple aborts the batch, including collisions within one claim
and across two claims; tests cover both cases.

- [ ] **Step 3: Write failing batch/runtime tests**

Use recording fakes to assert exact canonical claim order and calls:

```python
retriever.two_stage_retrieve(
    request.query,
    top_k=request.top_k,
    collection=plan.collection,
    filters={"kb_book_id": request.kb_book_id},
    query_mode="evidence",
)
```

Assert no ingest/upsert/delete/promote/sync member is ever accessed. Bind the
probe ID exactly as `probe:vfl:s1:<sha256>` over canonical sorted-key JSON with
these exact keys: `policy_version`, `plan_sha256`, `plan_id`, `execution_scope`, `request_id`,
`source_id`, `claim_id`, `query`, `top_k`, `collection`,
`expected_corpus_version`, `observed_corpus_version`,
`upstream_provenance_sha256`, `corpus_provenance`,
`source_snapshot_sha256`, `response_schema_versions` (exact tuple
`("kb-retrieve/v2", "kb-two-stage/v2", "kb-retrieve/v2")` in
stage-1/wrapper/nested-official order, retaining the duplicate)
and `evidence_references` (canonical sorted complete reference objects). The
retrieval-version digest has its smaller exact payload below. Mutation tests
hold `plan_sha256` fixed and independently change every probe-ID payload field
to prove no field is bound only indirectly. A changed semantic
manifest/ingest/meta projection field must change the probe and S0 run identity
even when the corpus-version string remains the same; changes confined to
operational `run_stats` must not. Recording fakes must provide the same explicit
provenance SHA/source fields and may not rely on adapter defaults.
Use two fresh validated meta sessions to assert that a `run_stats`-only change
preserves the persisted provenance digest, probe and S0 run identity, while a
change to any semantic provenance-projection field changes all three.

Notes are the following exact `key=value` strings in this fixed order only:
`plan_id`, `request_id`, `collection`, `expected_corpus_version`,
`observed_corpus_version`, `upstream_provenance_sha256`,
`corpus_provenance=upstream_meta`, `top_k`, `exact_candidate_count`,
`citable_count`, `source_snapshot_sha256`, followed by one
`rejected.<status>=<nonnegative-decimal>` entry for every resolver rejection
status in the exact allowlist order stated in Step 1. Plan SHA, query, other
request fields and response schemas belong to identity preimages/the probe's
existing explicit fields, never notes. Tests assert exact list equality and
reject extra, reordered, text/path/score/latency/error fields. Every produced probe is unresolved
and every reference is context-only. Duplicate inputs, partial second-query
failure, snapshot postflight drift and resolver failure expose neither a probe
batch nor a package/output directory.

Probe-ID tests add/remove a reference and independently change its locator or
evidence hash and require a different ID. Permuting hits or adding an identical
duplicate must preserve the canonical validated exact-hit tuple,
`exact_candidate_count`, exact notes, canonical reference tuple and probe/run
identity; no input-order bytes enter an identity preimage.

`plan_sha256` and `source_snapshot_sha256` are always the respective
`StrictJSONDocument.canonical_sha256` values. Their `raw_sha256` values never
enter a retriever call, probe preimage, retrieval version, note or S0 run
identity. Tests load semantically identical documents with different whitespace
and object-key order, assert different raw hashes but identical canonical
hashes/probe/run identity, then change one semantic field and require identity
change.

Encode `retrieval_version` exactly as
`vfl-readonly-probe/1.0.0:sha256:<64 lowercase hex>`, where the digest is over
canonical sorted-key JSON with exactly `policy_version`, `plan_sha256`,
`upstream_provenance_sha256`, `corpus_provenance`,
`source_snapshot_sha256` and `response_schema_versions`. The provenance source
is exactly `upstream_meta`; schema versions are exactly the same three-item
tuple and are never deduplicated or derived from hit/input order. Tests
assert length `<=256` and change each input independently to require a different
digest. The detailed safe hashes remain separately present in the probe-ID
preimage and deterministic notes; no value is dropped merely to fit the S0
field.

Within the request loop, map retriever, envelope, projection and resolver
failures to a new safe `ReadOnlyAdapterError` that preserves the allowlisted
enum code, sets `failed_claim_id=request.claim_id`, and uses `from None` so no
unsafe cause is retained. First- and second-request tests assert the exact
current claim ID. Plan/audit/snapshot preflight and postflight errors occur
outside a request and keep `failed_claim_id=None`; CLI tests prove it prints a
claim only after validating that value as a `StableId`.

Run the batch tests RED before implementation:

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)/apps/star-omen"
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
  ../../.venv/bin/python -m pytest -q \
  tests/video_pipeline/feedback_loop/test_readonly_runtime_v1.py
```

Expected: import failure because the complete-batch runtime does not exist.

- [ ] **Step 4: Implement complete-batch orchestration**

```text
build_local_evidence_probes(
    *,
    audit_bundle: ExternalAuditBundleV1,
    query_plan: LocalEvidenceQueryPlanV1,
    plan_sha256: str,
    retriever: ReadOnlyTwoStageRetriever,
    kb_root: Path,
    source_snapshot: LocalKBSourceSnapshotV1,
    source_snapshot_sha256: str,
    source_accessor: LocalKBSourceAccessor,
    resolver_context: EvidenceResolverContext,
    resolver: Callable[..., Mapping[str, object]] = resolve_evidence,
) -> tuple[LocalEvidenceProbeV1, ...]
```

Before retrieval, recompute canonical plan and snapshot SHA-256 values and
require exact equality with the supplied values. Require
`retriever.source_binding` (also mandatory on the recording fake protocol) to
equal `source_accessor.binding`, then call
`source_accessor.assert_bound(...)`. Tests prove plan-hash, snapshot-hash,
root-binding and snapshot-binding mismatches fail before the first retrieval.
Preflight the snapshot, compute all probes in memory, postflight the snapshot,
then return the immutable tuple. The runtime does not write a probe-only
artifact. The context is mandatory and forwarded unchanged on every resolver
call; tests install a fail-fast `get_settings` spy and assert the exact context
object. Test collections remain available only through the recording-fake test
constructor.

- [ ] **Step 5: Verify and deliver Task 4**

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)/apps/star-omen"
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
  ../../.venv/bin/python -m pytest -q \
  tests/video_pipeline/feedback_loop/test_readonly_adapter_v1.py \
  tests/video_pipeline/feedback_loop/test_readonly_runtime_v1.py \
  tests/video_pipeline/feedback_loop/test_readonly_contracts_v1.py \
  tests/video_pipeline/feedback_loop/test_source_snapshot_v1.py \
  tests/video_pipeline/feedback_loop/test_readonly_kb_v1.py
cd "$(git rev-parse --show-toplevel)"
git diff --check
git add apps/star-omen/src/video_pipeline/feedback_loop/readonly_adapter_v1.py \
  apps/star-omen/src/video_pipeline/feedback_loop/readonly_runtime_v1.py \
  apps/star-omen/tests/video_pipeline/feedback_loop/test_readonly_adapter_v1.py \
  apps/star-omen/tests/video_pipeline/feedback_loop/test_readonly_runtime_v1.py
test "$(git symbolic-ref --short HEAD)" = codex/kaiyuan-feedback-loop-readonly-adapters-v1
git diff --cached --check
test "$(git diff --cached --name-only)" = "$(printf '%s\n' \
  apps/star-omen/src/video_pipeline/feedback_loop/readonly_adapter_v1.py \
  apps/star-omen/src/video_pipeline/feedback_loop/readonly_runtime_v1.py \
  apps/star-omen/tests/video_pipeline/feedback_loop/test_readonly_adapter_v1.py \
  apps/star-omen/tests/video_pipeline/feedback_loop/test_readonly_runtime_v1.py)"
git commit -m "feat: build deterministic readonly evidence probes"
S1_STATUS=$(git status --porcelain)
test -z "$S1_STATUS"
```

Push/read back the exact remote tree before Task 5.

---

### Task 5: Add the episode 22 fixture, CLI, Make target and hermetic E2E

**Files:**

- Create: `apps/star-omen/scripts/run_video_feedback_loop_s1.py`
- Create:
  `apps/star-omen/tests/video_pipeline/feedback_loop/test_s1_cli_v1.py`
- Create:
  `tests/fixtures/video-feedback-loop/v1/episode-22-query-plan.json`
- Modify:
  `apps/star-omen/tests/video_pipeline/feedback_loop/test_fixture_assets_v1.py`
- Modify: `tests/fixtures/video-feedback-loop/v1/manifest.json`
- Modify: `Makefile`

**Interfaces:**

- Consumes: Tasks 1–4 public internal adapters and existing
  `build_feedback_loop_run(*, audit_bundle, local_probes, outcome=None)` /
  `publish_feedback_loop_run(*, output_dir, build)` S0 APIs.
- Produces: episode-22-only `run_video_feedback_loop_s1.py`, canonical
  `episode-22-query-plan.json`, and literal-safe `make vfl-s1-run` with exactly
  five public `VFL_S1_*` path variables.

- [ ] **Step 1: Write the canonical hermetic plan fixture and failing asset tests**

The fixture contains exactly the two episode 22 claim/query mappings in
canonical claim order, `kb_book_id="kaiyuan_zhanjing"`,
`execution_scope="hermetic_test"`,
`collection="test_vfl_ephemeral_episode_22"`, hermetic expected corpus
`20260902T000000Z` (the normal-ingest producer's timestamp grammar), policy
`vfl-readonly-probe/1.0.0` and `top_k=8`. This is explicitly a recording-fake
test fixture, not a live release-manifest attestation. Update the existing fixture manifest
with its established `path` plus raw-file `sha256` entry and assert the exact
three-file set. Do not add an unversioned size field, source snapshot or corpus
bytes.

Freeze `plan_id="query-plan:vfl:zushan:episode-22:v1"` and these requests:

```text
query-request:vfl:zushan:episode-22:01
  claim:douyin:zushan:episode-22:01
  毕宿 烈风 古典原文 来源
query-request:vfl:zushan:episode-22:02
  claim:douyin:zushan:episode-22:02
  烈风 海上风暴 古典对应关系
```

Both requests repeat the plan source/audit/book identities and
`query_mode="evidence"`; changing any ID or query changes the plan identity.
Hermetic E2E creates a matching temporary snapshot and recording meta with the
same ephemeral collection/corpus; the public production binder must reject this
fixture before any credential or network seam is touched.

- [ ] **Step 2: Write failing CLI and Make tests**

The CLI exposes exactly five required flags:

```text
--audit --query-plan --kb-root --source-snapshot --output
```

It has no probes, outcome, collection, corpus, base-url or api-key override.
Before constructing a retriever it validates all inputs and exact pilot IDs:

```text
source  media:douyin:zushan:collection-7664842437629921326:episode-22
audit   audit:douyin:zushan:episode-22
work    7669807398794598565
book    kaiyuan_zhanjing (plan and both requests)
```

Reject any other/missing plan or request book ID before credential resolution,
transport construction or network access; this is a public pilot-CLI gate, not
a claim that the internal adapter can never support another reviewed book.

Success prints only a safe run ID. Failure prints only a typed safe code and,
when applicable, an already validated claim ID. Neither stdout/stderr nor
package bytes may contain an API key, raw response body, newly read source
text, KB root or absolute source path.

A CLI/package adversary supplies a corpus-version sentinel rejected by the
shared `CorpusVersion` pre-validator and proves that sentinel cannot enter
notes, stdout, stderr, output files or staging paths.

Construct a non-abbreviating `SafeArgumentParser` whose `error()` ignores the
standard message and raises `ReadOnlyAdapterError(INVALID_LOCAL_INPUT)` from no
cause; wrap parser creation and `parse_args()` inside the same safe outer
boundary as runtime execution. Unknown options (including `--api-key` plus a
sentinel), missing option values, unexpected positionals and private option
abbreviations must exit nonzero with only the fixed safe code and must not echo
any argv value. Normal `--help` may print only the five public flags.

Create two fresh temporary outputs with a recording retriever and temporary
snapshot; assert identical relative member bytes/hashes and run ID. Replaying
into an occupied output must preserve the whole tree and leave no staging
residue. A second-request failure leaves no partial probes, directory or
staging path.

Use these exact E2E node names so the final gate can replay them directly:

```text
test_s1_cli_v1.py::test_episode_22_two_fresh_builds_emit_safe_hash_evidence
test_s1_cli_v1.py::test_occupied_output_preserves_tree_and_leaves_no_staging
test_s1_cli_v1.py::test_second_request_failure_leaves_no_output_or_staging
test_s1_cli_v1.py::test_stdout_stderr_and_package_add_no_retrieval_secrets
test_s1_cli_v1.py::test_public_reviewed_live_make_uses_real_factory_and_loopback_stub
```

The first node prints one allowlisted line under `pytest -s` containing only
`run_id`, manifest SHA-256 and canonical relative-member path/hash-list SHA-256;
the collision node records equal before/after tree SHA-256 and zero staging
entries. No temporary or absolute path is printed.

Keep production and hermetic entry paths structurally separate. Production
`main(argv)` performs safe parse → strict loads → production binder (therefore
`reviewed_live`) → snapshot binding/accessor → production retriever factory,
then calls one shared internal complete-batch/build/publish function. It has no
retriever injection argument. In `test_s1_cli_v1.py` only, define a private
`_run_hermetic_s1(...)` helper that requires `type(retriever) is` the concrete
test `RecordingTwoStageRetriever`, requires the hermetic/ephemeral pair through
the test binder, binds the matching temporary snapshot, and then invokes that
same shared core. The four named hermetic evidence nodes use this test-owned
helper; they never monkeypatch the production binder/factory. Separate public
CLI tests pass the committed fixture and prove rejection, plus zero credential,
transport and network calls, before exercising parser and production ordering.

The fifth named node is a mandatory hermetic production-wiring success test,
not one of the four printed evidence records. Start a test-owned
`ThreadingHTTPServer` on literal `127.0.0.1` with an OS-assigned port and
suppressed request logging. It serves stable strict `/v1/meta` bytes and exact
deployed `RetrieveResponse` JSON for both stage requests, validates method,
path, payload and both credential headers, and returns a snippet-only primary
hit whose real parser offsets/hashes identify one passage in the temporary
snapshot. Assemble the secret from non-token fragments at runtime. Create a
temporary `execution_scope=reviewed_live` plan for `local_kb_kaiyuan_v2`,
matching snapshot and meta; do not use or modify the committed hermetic
fixture. Invoke the real root `make -s vfl-s1-run PYTHON=<current interpreter>
...` in a subprocess with `KB_SEARCH_BASE_URL`/`KB_SEARCH_API_KEY`, while
clearing `APP_CONFIG_PATH` so the module-derived absolute default config is
exercised from repository root. Do not inject or monkeypatch the binder,
factory, retriever, transport or shared core. Require exit 0, one safe run ID,
exact request counts/order, a valid atomic package and no server/thread/staging
residue. A companion public-`main(argv)` run from an unrelated CWD uses a fresh
output and the same kind of local stub to prove identical default config
resolution. This local process-I/O test does not count as the optional real
Local-KB smoke.

For `vfl-s1-run`, mirror S0's literal-safe Make boundary with the five public
variables `VFL_S1_AUDIT`, `VFL_S1_QUERY_PLAN`, `VFL_S1_KB_ROOT`,
`VFL_S1_SOURCE_SNAPSHOT` and `VFL_S1_OUTPUT`; use `unexport`, target-specific
private override exports that copy the five public values through exact
`$(value VFL_S1_AUDIT)`, `$(value VFL_S1_QUERY_PLAN)`, `$(value
VFL_S1_KB_ROOT)`, `$(value VFL_S1_SOURCE_SNAPSHOT)` and `$(value
VFL_S1_OUTPUT)` expressions, shell non-empty checks and `set --`. Add
`vfl-s1-run` to
`.PHONY`. Tests use an argv-recording Python shim and cover spaces, quotes,
backticks, dollar signs, Make function text remaining literal (including a
literal shell-function expression), and attempts to override the five private
aliases. Keep `vfl-s0-run` unchanged and rerun its tests.

Run RED:

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)/apps/star-omen"
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
  ../../.venv/bin/python -m pytest -q \
  tests/video_pipeline/feedback_loop/test_s1_cli_v1.py \
  tests/video_pipeline/feedback_loop/test_fixture_assets_v1.py \
  tests/video_pipeline/feedback_loop/test_cli_v1.py
```

Expected: the S1 CLI/fixture imports and `vfl-s1-run` assertions fail because
the entry point, canonical hermetic query plan and Make target do not exist.

- [ ] **Step 3: Implement the CLI**

Load audit/plan/snapshot with strict loaders, bind plan to audit, call
`bind_source_snapshot_to_plan()` for exact collection/book/corpus equality,
then open the snapshot accessor and build the production S1 retriever. These
bindings all complete before credential resolution, accessor construction or
retrieval. Pass `session.resolver_context` explicitly through the shared core
to the complete-batch runtime; neither the CLI nor resolver calls
`get_settings()` again. The private hermetic helper supplies its own fixed safe
context and asserts the exact object reaches every recording resolver. Produce the complete
probe tuple by passing `plan_sha256=plan_doc.canonical_sha256` and
`source_snapshot_sha256=snapshot_doc.canonical_sha256`; never pass either
document's `raw_sha256`. Assert the snapshot is unchanged, then and only then call:

```python
build = build_feedback_loop_run(
    audit_bundle=audit.value,
    local_probes=probes,
    outcome=None,
)
publish_feedback_loop_run(output_dir=args.output, build=build)
```

Keep S0's package-member set and atomic no-replace semantics unchanged.

The committed query-plan fixture is used only by hermetic E2E. A real smoke
requires a separate caller-supplied, reviewed episode-22 plan whose exact
`expected_corpus_version` matches both the supplied snapshot and the currently
served immutable release manifest. The CLI never derives or rewrites that
value from `/v1/meta`; if the live plan is absent or mismatched the smoke is
`BLOCKED`/rejected, never silently redirected to the fixture.

- [ ] **Step 4: Verify and deliver Task 5**

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)/apps/star-omen"
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
  ../../.venv/bin/python -m pytest -q \
  tests/video_pipeline/feedback_loop/test_readonly_contracts_v1.py \
  tests/video_pipeline/feedback_loop/test_readonly_inputs_v1.py \
  tests/video_pipeline/feedback_loop/test_source_snapshot_v1.py \
  tests/video_pipeline/feedback_loop/test_readonly_kb_v1.py \
  tests/video_pipeline/feedback_loop/test_readonly_adapter_v1.py \
  tests/video_pipeline/feedback_loop/test_readonly_runtime_v1.py \
  tests/video_pipeline/feedback_loop/test_s1_cli_v1.py \
  tests/video_pipeline/feedback_loop/test_fixture_assets_v1.py
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
  ../../.venv/bin/python -m pytest -q tests/video_pipeline/feedback_loop
cd "$(git rev-parse --show-toplevel)"
git diff --check
git add Makefile apps/star-omen/scripts/run_video_feedback_loop_s1.py \
  apps/star-omen/tests/video_pipeline/feedback_loop/test_s1_cli_v1.py \
  apps/star-omen/tests/video_pipeline/feedback_loop/test_fixture_assets_v1.py \
  tests/fixtures/video-feedback-loop/v1/episode-22-query-plan.json \
  tests/fixtures/video-feedback-loop/v1/manifest.json
test "$(git symbolic-ref --short HEAD)" = codex/kaiyuan-feedback-loop-readonly-adapters-v1
git diff --cached --check
test "$(git diff --cached --name-only)" = "$(printf '%s\n' \
  Makefile \
  apps/star-omen/scripts/run_video_feedback_loop_s1.py \
  apps/star-omen/tests/video_pipeline/feedback_loop/test_fixture_assets_v1.py \
  apps/star-omen/tests/video_pipeline/feedback_loop/test_s1_cli_v1.py \
  tests/fixtures/video-feedback-loop/v1/episode-22-query-plan.json \
  tests/fixtures/video-feedback-loop/v1/manifest.json)"
git commit -m "feat: add episode 22 readonly feedback loop CLI"
S1_STATUS=$(git status --porcelain)
test -z "$S1_STATUS"
```

Push/read back the exact remote tree before Task 6.

---

### Task 6: Complete verification, independent review and governance closeout

**Files:**

- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/DECISIONS.md`
- Modify: `docs/development/PROJECT_MEMORY.md`
- Modify: `docs/development/WORK_LOG.md`
- Modify: `summary.md`
- Modify this plan only to record exact execution evidence if needed.

**Interfaces:**

- Consumes: the exact Task 1–5 commit range, task reports/reviews, hermetic E2E
  hashes, governance state and fetched remote refs.
- Produces: VFL-T02 `VERIFYING` then `DONE` durable records, one clean final
  reviewed S1 head/tree and exact non-force remote readback; no PR or merge.

- [ ] **Step 1: Move VFL-T02 to VERIFYING**

Record the exact implementation head/tree and task commit sequence. Do not mark
`DONE` yet. Commit and push/read back this narrow state transition if required
by the repository's governance checker.

- [ ] **Step 2: Run the complete local verification matrix**

The four named E2E nodes emit these exact, allowlisted evidence records under
`pytest -s` (pytest's own progress and summary lines are ignored):

```text
S1_E2E_HASH_EVIDENCE run_id=<stable-id> manifest_sha256=<64hex> member_hash_list_sha256=<64hex>
S1_OCCUPIED_OUTPUT_EVIDENCE before_tree_sha256=<64hex> after_tree_sha256=<same-64hex> staging_entries=0
S1_SECOND_REQUEST_FAILURE_EVIDENCE output_exists=false staging_entries=0
S1_PRIVACY_EVIDENCE fields=api_key,raw_response_body,retrieved_text,kb_root,absolute_source_path surfaces=stdout,stderr,package status=PASS
```

Run and capture the exact records in a controller-owned temporary log, then
validate every required record and equality before copying those four lines
verbatim into the task report and final work log:

```bash
set -euo pipefail
S1_EVIDENCE_LOG="$(mktemp)"
trap 'rm -f "$S1_EVIDENCE_LOG"' EXIT
cd "$(git rev-parse --show-toplevel)/apps/star-omen"
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
  ../../.venv/bin/python -m pytest -q -s \
  tests/video_pipeline/feedback_loop/test_s1_cli_v1.py::test_episode_22_two_fresh_builds_emit_safe_hash_evidence \
  tests/video_pipeline/feedback_loop/test_s1_cli_v1.py::test_occupied_output_preserves_tree_and_leaves_no_staging \
  tests/video_pipeline/feedback_loop/test_s1_cli_v1.py::test_second_request_failure_leaves_no_output_or_staging \
  tests/video_pipeline/feedback_loop/test_s1_cli_v1.py::test_stdout_stderr_and_package_add_no_retrieval_secrets | \
  tee "$S1_EVIDENCE_LOG"
../../.venv/bin/python - "$S1_EVIDENCE_LOG" <<'PY'
import re
import sys
from pathlib import Path

lines = Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
evidence_lines = [
    line for line in lines if line.startswith("S1_") and "_EVIDENCE " in line
]
if len(evidence_lines) != 4:
    raise SystemExit("unexpected S1 evidence record count")
patterns = {
    "hash": re.compile(
        r"^S1_E2E_HASH_EVIDENCE run_id=[A-Za-z0-9][A-Za-z0-9._:/-]* "
        r"manifest_sha256=([0-9a-f]{64}) member_hash_list_sha256=([0-9a-f]{64})$"
    ),
    "occupied": re.compile(
        r"^S1_OCCUPIED_OUTPUT_EVIDENCE before_tree_sha256=([0-9a-f]{64}) "
        r"after_tree_sha256=([0-9a-f]{64}) staging_entries=0$"
    ),
    "failure": re.compile(
        r"^S1_SECOND_REQUEST_FAILURE_EVIDENCE output_exists=false staging_entries=0$"
    ),
    "privacy": re.compile(
        r"^S1_PRIVACY_EVIDENCE "
        r"fields=api_key,raw_response_body,retrieved_text,kb_root,absolute_source_path "
        r"surfaces=stdout,stderr,package status=PASS$"
    ),
}
matches = {
    name: [pattern.fullmatch(line) for line in evidence_lines]
    for name, pattern in patterns.items()
}
if any(
    sum(match is not None for match in values) != 1
    for values in matches.values()
):
    raise SystemExit("missing or duplicate S1 evidence record")
if any(
    sum(pattern.fullmatch(line) is not None for pattern in patterns.values()) != 1
    for line in evidence_lines
):
    raise SystemExit("non-allowlisted S1 evidence record")
occupied = next(match for match in matches["occupied"] if match is not None)
if occupied.group(1) != occupied.group(2):
    raise SystemExit("occupied output tree changed")
PY
cd "$(git rev-parse --show-toplevel)"
```

The privacy node is the field-aware scan: it constructs sentinel values for
each named forbidden field, checks structured stdout, stderr and every
published package member independently, and emits `status=PASS` only after all
five sentinels are absent from all three surfaces. This is deliberately more
precise than a broad scan that would reject the approved S0 audit URL, creator
locator or short `exact_text`. Token-shaped test sentinels are assembled from
separate fragments at runtime so no credential-shaped literal enters tracked
test bytes; the all-changed-bytes static secret scan below therefore includes
the test tree without false-pass exclusions.

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)/apps/star-omen"
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
  ../../.venv/bin/python -m pytest -q \
  tests/video_pipeline/feedback_loop \
  tests/video_pipeline/external_media \
  tests/test_config.py \
  tests/test_retriever.py \
  tests/test_kaiyuan_retrieval_v2.py \
  tests/test_official_two_stage_v2.py \
  tests/test_observability_v2.py \
  tests/test_transport_error_taxonomy_v2.py \
  tests/test_transport_security_v2.py \
  tests/test_primary_passage_cache_v2.py \
  tests/test_evidence_resolver.py \
  tests/test_citable_evidence_v2.py \
  tests/video_pipeline/package_review/test_package_atomic_v1.py \
  tests/video_pipeline/package_review/test_vertical_package_e2e_v1.py
cd "$(git rev-parse --show-toplevel)"
env -u CODEX_PRIMARY_RUNTIME_PYTHON PATH="$PWD/.venv/bin:$PATH" make downstream-test
.venv/bin/python -m compileall -q \
  apps/star-omen/src apps/star-omen/scripts apps/star-omen/tests
.venv/bin/python -m unittest discover -s scripts/tests -p 'test_*.py' -v
.venv/bin/python scripts/check_development_governance.py \
  --root . \
  --base e087d5e627bcb3e838e49015c61a3f74c0a5a2e8 \
  --head HEAD
.venv/bin/python scripts/check_development_governance.py \
  --root . \
  --base 99c0a85c1f944add8d013aedbae830fe022b7c3b \
  --head HEAD
git diff --check e087d5e627bcb3e838e49015c61a3f74c0a5a2e8..HEAD
git diff --name-status e087d5e627bcb3e838e49015c61a3f74c0a5a2e8..HEAD
git diff --name-only -z e087d5e627bcb3e838e49015c61a3f74c0a5a2e8..HEAD | \
  .venv/bin/python -c 'import re,sys; allowed=(r"^Makefile$",r"^summary\.md$",r"^docs/development/(TASKS|DECISIONS|PROJECT_MEMORY|WORK_LOG)\.md$",r"^docs/superpowers/plans/2026-09-02-kaiyuan-feedback-loop-readonly-adapters\.md$",r"^docs/superpowers/specs/2026-09-02-kaiyuan-feedback-loop-readonly-adapters-design\.md$",r"^apps/star-omen/scripts/run_video_feedback_loop_s1\.py$",r"^apps/star-omen/src/config/(settings|__init__)\.py$",r"^apps/star-omen/src/connectors/(primary_passage_cache|primary_file_scanner|evidence_resolver)\.py$",r"^apps/star-omen/src/connectors/kb_retrieval/(transport|client|core|two_stage)\.py$",r"^apps/star-omen/src/video_pipeline/feedback_loop/(readonly_contracts_v1|strict_local_files|source_snapshot_v1|readonly_kb_v1|readonly_adapter_v1|readonly_runtime_v1)\.py$",r"^apps/star-omen/tests/(test_config|test_retriever|test_kaiyuan_retrieval_v2|test_official_two_stage_v2|test_transport_error_taxonomy_v2|test_transport_security_v2|test_primary_passage_cache_v2|test_evidence_resolver|test_citable_evidence_v2)\.py$",r"^apps/star-omen/tests/video_pipeline/feedback_loop/(test_readonly_contracts_v1|test_readonly_inputs_v1|test_source_snapshot_v1|test_readonly_kb_v1|test_readonly_adapter_v1|test_readonly_runtime_v1|test_s1_cli_v1|test_fixture_assets_v1)\.py$",r"^tests/fixtures/video-feedback-loop/v1/(episode-22-query-plan|manifest)\.json$"); paths=[raw.decode("utf-8","strict") for raw in sys.stdin.buffer.read().split(b"\0") if raw]; bad=[p for p in paths if not any(re.fullmatch(a,p) for a in allowed)]; sys.exit("unexpected changed paths: "+repr(bad) if bad else 0)'
git merge-base --is-ancestor e087d5e627bcb3e838e49015c61a3f74c0a5a2e8 HEAD
git merge-base --is-ancestor 99c0a85c1f944add8d013aedbae830fe022b7c3b \
  e087d5e627bcb3e838e49015c61a3f74c0a5a2e8
git diff --exit-code e087d5e627bcb3e838e49015c61a3f74c0a5a2e8..HEAD -- \
  apps/local-kb-unified corpus packages/kb-contracts packages/kb-text-core .github
git diff --exit-code e087d5e627bcb3e838e49015c61a3f74c0a5a2e8..HEAD -- \
  apps/star-omen/src/video_pipeline/feedback_loop/contracts_v1.py \
  apps/star-omen/src/video_pipeline/feedback_loop/comparison.py \
  apps/star-omen/src/video_pipeline/feedback_loop/planner.py \
  apps/star-omen/src/video_pipeline/feedback_loop/orchestrator.py \
  apps/star-omen/scripts/run_video_feedback_loop.py
if rg -n '\b(ingest|upsert|delete|promote|sync_candidates)\s*\(' \
  apps/star-omen/src/video_pipeline/feedback_loop/readonly_* \
  apps/star-omen/scripts/run_video_feedback_loop_s1.py; then
  exit 1
else
  test "$?" -eq 1
fi
if rg -n '(^|[[:space:]])(import|from)[[:space:]]+(requests|playwright|selenium|yt_dlp)' \
  apps/star-omen/src/video_pipeline/feedback_loop/readonly_* \
  apps/star-omen/scripts/run_video_feedback_loop_s1.py; then
  exit 1
else
  test "$?" -eq 1
fi
S1_STATIC_DIFF="$(mktemp)"
S1_SURFACE_DIFF="$(mktemp)"
S1_RUNTIME_DIFF="$(mktemp)"
trap 'rm -f "$S1_STATIC_DIFF" "$S1_SURFACE_DIFF" "$S1_RUNTIME_DIFF"' EXIT
git diff --unified=0 e087d5e627bcb3e838e49015c61a3f74c0a5a2e8..HEAD -- \
  apps/star-omen tests/fixtures Makefile docs summary.md \
  >"$S1_STATIC_DIFF"
git diff --unified=0 e087d5e627bcb3e838e49015c61a3f74c0a5a2e8..HEAD -- \
  apps/star-omen/src apps/star-omen/scripts tests/fixtures Makefile docs summary.md \
  >"$S1_SURFACE_DIFF"
git diff --unified=0 e087d5e627bcb3e838e49015c61a3f74c0a5a2e8..HEAD -- \
  apps/star-omen/src apps/star-omen/scripts tests/fixtures Makefile \
  >"$S1_RUNTIME_DIFF"
.venv/bin/python - "$S1_STATIC_DIFF" "$S1_SURFACE_DIFF" "$S1_RUNTIME_DIFF" <<'PY'
import re
import sys
from pathlib import Path

added = [
    line[1:]
    for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
    if line.startswith("+") and not line.startswith("+++")
]
surface_added = [
    line[1:]
    for line in Path(sys.argv[2]).read_text(encoding="utf-8").splitlines()
    if line.startswith("+") and not line.startswith("+++")
]
runtime_added = [
    line[1:]
    for line in Path(sys.argv[3]).read_text(encoding="utf-8").splitlines()
    if line.startswith("+") and not line.startswith("+++")
]
secret_patterns = (
    re.compile(re.escape("github" + "_pat_") + r"[A-Za-z0-9_]{30,}"),
    re.compile(re.escape("gh" + "p_") + r"[A-Za-z0-9]{30,}"),
    re.compile(re.escape("s" + "k-") + r"[A-Za-z0-9_-]{20,}"),
    re.compile(re.escape("Bear" + "er ") + r"[A-Za-z0-9._~-]{16,}"),
)
machine_markers = ("/" + "workspace" + "/", "/" + "home" + "/")
has_secret = any(pattern.search(line) for line in added for pattern in secret_patterns)
has_machine_path = any(
    marker in line for line in surface_added for marker in machine_markers
)
has_windows_home = any(
    re.search(r"[A-Za-z]:\\Users\\", line) for line in surface_added
)
has_forbidden_collection = any("local_kb_default" in line for line in runtime_added)
mutation_call = re.compile(
    r"\b(ingest|upsert|delete|promote|sync_candidates)\s*\("
)
platform_import = re.compile(
    r"(^|\s)(import|from)\s+(requests|playwright|selenium|yt_dlp)(?:\b|\.)"
)
has_mutation_call = any(mutation_call.search(line) for line in runtime_added)
has_platform_import = any(platform_import.search(line) for line in runtime_added)
if (
    has_secret
    or has_machine_path
    or has_windows_home
    or has_forbidden_collection
    or has_mutation_call
    or has_platform_import
):
    raise SystemExit("static S1 secret, path, collection, mutation or platform scan failed")
PY
S1_STATUS=$(git status --porcelain)
test -z "$S1_STATUS"
```

Run field-aware privacy/secret scans over changed tracked bytes. The approved
audit URL, creator locator and short `exact_text` remain legitimate S0 fields;
the scan must specifically prove no newly retrieved/resolver text, raw body,
credential, KB root or absolute source path entered S1 output, logs or fixtures.

Run the hermetic E2E twice and record run ID, manifest SHA-256 and canonical
member path/hash-list SHA-256. Record the occupied-output tree before/after and
zero staging residue. Do not run a real local-KB smoke unless a caller-supplied
reviewed live plan, matching source snapshot and the literal-loopback service
are all available; otherwise record exactly `BLOCKED: caller-supplied reviewed
live plan, matching source snapshot or literal-loopback service absent`. That environment block does not invalidate
hermetic S1 completion, but it blocks S2 consumption of real S1 output.

- [ ] **Step 3: Request independent reviews**

Use a fresh reviewer for the complete implementation range. Require explicit
counts for Critical, Important and Minor findings and spec/governance coverage.
Fix every Critical or Important finding with a new RED test and focused commit,
push/read back that fix, rerun all affected and complete gates, then obtain a
scoped re-review. B10 Reviewer B is not this code reviewer.

- [ ] **Step 4: Close durable state**

Update VFL-T02 from `VERIFYING` to `DONE` only after all hermetic gates and
independent review have no unresolved Critical or Important finding. Record:

- exact local/remote Task 1–5 implementation commits/trees and the Task 6
  pre-closeout parent/tree; the closeout commit cannot self-contain its own
  SHA/tree;
- every task commit and remote readback;
- exact test counts and commands;
- deterministic package/run hashes and collision evidence;
- privacy/scope/ancestry/governance results;
- real smoke `PASSED` or accurately `BLOCKED`;
- Runner `NOT RUN`, no PR/merge/stable/main/PR #54/media/account side effect;
- B10 Reviewer B still parked as the terminal independent human gate.

Run governance, diff, scope, secret/path and clean-status checks again on the
final documentation head.

- [ ] **Step 5: Commit and deliver closeout**

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
git add docs/development/TASKS.md docs/development/DECISIONS.md \
  docs/development/PROJECT_MEMORY.md docs/development/WORK_LOG.md summary.md \
  docs/superpowers/plans/2026-09-02-kaiyuan-feedback-loop-readonly-adapters.md
test "$(git symbolic-ref --short HEAD)" = codex/kaiyuan-feedback-loop-readonly-adapters-v1
git diff --cached --check
test "$(git diff --cached --name-only)" = "$(printf '%s\n' \
  docs/development/DECISIONS.md \
  docs/development/PROJECT_MEMORY.md \
  docs/development/TASKS.md \
  docs/development/WORK_LOG.md \
  docs/superpowers/plans/2026-09-02-kaiyuan-feedback-loop-readonly-adapters.md \
  summary.md)"
git commit -m "docs: close readonly feedback loop adapters"
```

The documentation commit changes `HEAD`; therefore rerun the closeout gates on
that exact committed head before push:

```bash
set -euo pipefail
.venv/bin/python -m unittest discover -s scripts/tests -p 'test_*.py' -v
.venv/bin/python scripts/check_development_governance.py \
  --root . \
  --base e087d5e627bcb3e838e49015c61a3f74c0a5a2e8 \
  --head HEAD
.venv/bin/python scripts/check_development_governance.py \
  --root . \
  --base 99c0a85c1f944add8d013aedbae830fe022b7c3b \
  --head HEAD
git diff --check e087d5e627bcb3e838e49015c61a3f74c0a5a2e8..HEAD
git diff --name-only -z e087d5e627bcb3e838e49015c61a3f74c0a5a2e8..HEAD | \
  .venv/bin/python -c 'import re,sys; allowed=(r"^Makefile$",r"^summary\.md$",r"^docs/development/(TASKS|DECISIONS|PROJECT_MEMORY|WORK_LOG)\.md$",r"^docs/superpowers/plans/2026-09-02-kaiyuan-feedback-loop-readonly-adapters\.md$",r"^docs/superpowers/specs/2026-09-02-kaiyuan-feedback-loop-readonly-adapters-design\.md$",r"^apps/star-omen/scripts/run_video_feedback_loop_s1\.py$",r"^apps/star-omen/src/config/(settings|__init__)\.py$",r"^apps/star-omen/src/connectors/(primary_passage_cache|primary_file_scanner|evidence_resolver)\.py$",r"^apps/star-omen/src/connectors/kb_retrieval/(transport|client|core|two_stage)\.py$",r"^apps/star-omen/src/video_pipeline/feedback_loop/(readonly_contracts_v1|strict_local_files|source_snapshot_v1|readonly_kb_v1|readonly_adapter_v1|readonly_runtime_v1)\.py$",r"^apps/star-omen/tests/(test_config|test_retriever|test_kaiyuan_retrieval_v2|test_official_two_stage_v2|test_transport_error_taxonomy_v2|test_transport_security_v2|test_primary_passage_cache_v2|test_evidence_resolver|test_citable_evidence_v2)\.py$",r"^apps/star-omen/tests/video_pipeline/feedback_loop/(test_readonly_contracts_v1|test_readonly_inputs_v1|test_source_snapshot_v1|test_readonly_kb_v1|test_readonly_adapter_v1|test_readonly_runtime_v1|test_s1_cli_v1|test_fixture_assets_v1)\.py$",r"^tests/fixtures/video-feedback-loop/v1/(episode-22-query-plan|manifest)\.json$"); paths=[raw.decode("utf-8","strict") for raw in sys.stdin.buffer.read().split(b"\0") if raw]; bad=[p for p in paths if not any(re.fullmatch(a,p) for a in allowed)]; sys.exit("unexpected changed paths: "+repr(bad) if bad else 0)'
git diff --exit-code e087d5e627bcb3e838e49015c61a3f74c0a5a2e8..HEAD -- \
  apps/local-kb-unified corpus packages/kb-contracts packages/kb-text-core .github
git diff --exit-code e087d5e627bcb3e838e49015c61a3f74c0a5a2e8..HEAD -- \
  apps/star-omen/src/video_pipeline/feedback_loop/contracts_v1.py \
  apps/star-omen/src/video_pipeline/feedback_loop/comparison.py \
  apps/star-omen/src/video_pipeline/feedback_loop/planner.py \
  apps/star-omen/src/video_pipeline/feedback_loop/orchestrator.py \
  apps/star-omen/scripts/run_video_feedback_loop.py
S1_STATIC_DIFF="$(mktemp)"
S1_SURFACE_DIFF="$(mktemp)"
S1_RUNTIME_DIFF="$(mktemp)"
trap 'rm -f "$S1_STATIC_DIFF" "$S1_SURFACE_DIFF" "$S1_RUNTIME_DIFF"' EXIT
git diff --unified=0 e087d5e627bcb3e838e49015c61a3f74c0a5a2e8..HEAD -- \
  apps/star-omen tests/fixtures Makefile docs summary.md \
  >"$S1_STATIC_DIFF"
git diff --unified=0 e087d5e627bcb3e838e49015c61a3f74c0a5a2e8..HEAD -- \
  apps/star-omen/src apps/star-omen/scripts tests/fixtures Makefile docs summary.md \
  >"$S1_SURFACE_DIFF"
git diff --unified=0 e087d5e627bcb3e838e49015c61a3f74c0a5a2e8..HEAD -- \
  apps/star-omen/src apps/star-omen/scripts tests/fixtures Makefile \
  >"$S1_RUNTIME_DIFF"
.venv/bin/python - "$S1_STATIC_DIFF" "$S1_SURFACE_DIFF" "$S1_RUNTIME_DIFF" <<'PY'
import re
import sys
from pathlib import Path

added = [
    line[1:]
    for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
    if line.startswith("+") and not line.startswith("+++")
]
surface_added = [
    line[1:]
    for line in Path(sys.argv[2]).read_text(encoding="utf-8").splitlines()
    if line.startswith("+") and not line.startswith("+++")
]
runtime_added = [
    line[1:]
    for line in Path(sys.argv[3]).read_text(encoding="utf-8").splitlines()
    if line.startswith("+") and not line.startswith("+++")
]
secret_patterns = (
    re.compile(re.escape("github" + "_pat_") + r"[A-Za-z0-9_]{30,}"),
    re.compile(re.escape("gh" + "p_") + r"[A-Za-z0-9]{30,}"),
    re.compile(re.escape("s" + "k-") + r"[A-Za-z0-9_-]{20,}"),
    re.compile(re.escape("Bear" + "er ") + r"[A-Za-z0-9._~-]{16,}"),
)
machine_markers = ("/" + "workspace" + "/", "/" + "home" + "/")
has_secret = any(pattern.search(line) for line in added for pattern in secret_patterns)
has_machine_path = any(
    marker in line for line in surface_added for marker in machine_markers
)
has_windows_home = any(
    re.search(r"[A-Za-z]:\\Users\\", line) for line in surface_added
)
has_forbidden_collection = any("local_kb_default" in line for line in runtime_added)
mutation_call = re.compile(
    r"\b(ingest|upsert|delete|promote|sync_candidates)\s*\("
)
platform_import = re.compile(
    r"(^|\s)(import|from)\s+(requests|playwright|selenium|yt_dlp)(?:\b|\.)"
)
has_mutation_call = any(mutation_call.search(line) for line in runtime_added)
has_platform_import = any(platform_import.search(line) for line in runtime_added)
if (
    has_secret
    or has_machine_path
    or has_windows_home
    or has_forbidden_collection
    or has_mutation_call
    or has_platform_import
):
    raise SystemExit("static S1 secret, path, collection, mutation or platform scan failed")
PY
S1_STATUS=$(git status --porcelain)
test -z "$S1_STATUS"
```

Non-force push the final S1 head, fetch/read back exact ref and tree, and verify
stable, `main`, S0 branch and PR #54 remain unchanged. Do not create or merge a
PR. Leave the tracked worktree clean.

Before that final push, give a fresh scoped documentation reviewer the exact
final `HEAD`, implementation-review report, task reports and captured gate
output. Require it to verify that every recorded SHA/tree, test count, E2E
evidence line, smoke status and no-side-effect statement is supported, and to
report explicit Critical/Important/Minor counts. Push only when the reviewed
final documentation head remains unchanged with `0 Critical / 0 Important`.
If it finds a Critical or Important documentation error, correct it in a new
docs-only commit, rerun this entire post-commit gate and repeat the scoped
review. This makes the delivered closeout tree reviewed without treating that
reviewer as B10 Reviewer B.

After the connector delivery/readback, record the pre-delivery local closeout
SHA, connector-created remote SHA and shared reviewed tree in the SDD Task 6
report and controller handoff, together with the protected-ref and PR #54
readbacks. Do not create another tracked commit merely to embed its predecessor:
that would produce an endless self-reference chain. The fetched remote ref and
tree are the durable repository truth for the final closeout.

## Per-task non-force delivery and readback gate

The ordinary path is
`git push origin HEAD:codex/kaiyuan-feedback-loop-readonly-adapters-v1` with no
force option. The
current environment can fetch publicly but has no Git credential helper, so an
authorized GitHub connector may create one commit with the remote S1 head as
its single parent and the exact local task tree, then update only the S1 ref
with `force=false`. Never put a token in a command, URL, file or log.

Before either the ordinary push or connector delivery, record and mark:

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
BRANCH=codex/kaiyuan-feedback-loop-readonly-adapters-v1
git fetch origin "+refs/heads/$BRANCH:refs/remotes/origin/$BRANCH"
test "$(git symbolic-ref --short HEAD)" = "$BRANCH"
LOCAL_SHA=$(git rev-parse HEAD)
LOCAL_TREE=$(git rev-parse HEAD^{tree})
REMOTE_PARENT=$(git rev-parse "origin/$BRANCH")
git merge-base --is-ancestor "$REMOTE_PARENT" "$LOCAL_SHA"
DELIVERY_MARKER=refs/codex/s1-delivery-parent
if git show-ref --verify --quiet "$DELIVERY_MARKER"; then
  exit 1
else
  test "$?" -eq 1
fi
git update-ref "$DELIVERY_MARKER" "$REMOTE_PARENT"
```

Keep that local-only marker across the chosen remote update; it is never pushed. The
controller must delete it after readback or explicitly clean it before retrying
an interrupted delivery.

After the non-force remote update, fetch and prove tree equality:

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
BRANCH=codex/kaiyuan-feedback-loop-readonly-adapters-v1
test "$(git symbolic-ref --short HEAD)" = "$BRANCH"
LOCAL_SHA=$(git rev-parse HEAD)
LOCAL_TREE=$(git rev-parse HEAD^{tree})
DELIVERY_MARKER=refs/codex/s1-delivery-parent
DELIVERY_REMOTE_PARENT=$(git rev-parse "$DELIVERY_MARKER")
trap 'git update-ref -d "$DELIVERY_MARKER" >/dev/null 2>&1 || true' EXIT
git fetch origin \
  "+refs/heads/$BRANCH:refs/remotes/origin/$BRANCH"
REMOTE_SHA=$(git rev-parse "origin/$BRANCH")
test "$(git rev-parse "$REMOTE_SHA^{tree}")" = "$LOCAL_TREE"
REMOTE_PARENTS=$(git show -s --format=%P "$REMOTE_SHA")
if test "$REMOTE_SHA" = "$LOCAL_SHA"; then
  test "$(git rev-parse "$LOCAL_SHA^")" = "$DELIVERY_REMOTE_PARENT"
  test "$REMOTE_PARENTS" = "$(git rev-parse "$LOCAL_SHA^")"
else
  test "$REMOTE_PARENTS" = "$DELIVERY_REMOTE_PARENT"
fi
S1_REF_GUARDS="$(mktemp)"
trap 'rm -f "$S1_REF_GUARDS"; git update-ref -d "$DELIVERY_MARKER" >/dev/null 2>&1 || true' EXIT
git ls-remote --heads origin \
  refs/heads/main \
  refs/heads/stable/kaiyuan-v2 \
  refs/heads/codex/kaiyuan-evidence-feedback-loop-skeleton-v1 \
  >"$S1_REF_GUARDS"
.venv/bin/python - "$S1_REF_GUARDS" <<'PY'
import sys
from pathlib import Path

actual = {}
for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
    sha, ref = line.split("\t", 1)
    actual[ref] = sha
expected = {
    "refs/heads/main": "98e0bb713a164a384d890b273af47d3b9b444682",
    "refs/heads/stable/kaiyuan-v2": "99c0a85c1f944add8d013aedbae830fe022b7c3b",
    "refs/heads/codex/kaiyuan-evidence-feedback-loop-skeleton-v1": (
        "e087d5e627bcb3e838e49015c61a3f74c0a5a2e8"
    ),
}
if actual != expected:
    raise SystemExit("protected remote ref guard changed")
PY
git update-ref -d "$DELIVERY_MARKER" "$DELIVERY_REMOTE_PARENT"
trap - EXIT
rm -f "$S1_REF_GUARDS"
S1_STATUS=$(git status --porcelain)
test -z "$S1_STATUS"
```

When connector delivery necessarily creates a different commit SHA with the
same tree, realign the local branch only after the tree equality assertion:

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
BRANCH=codex/kaiyuan-feedback-loop-readonly-adapters-v1
test "$(git symbolic-ref --short HEAD)" = "$BRANCH"
LOCAL_SHA=$(git rev-parse HEAD)
LOCAL_TREE=$(git rev-parse HEAD^{tree})
REMOTE_SHA=$(git rev-parse "origin/$BRANCH")
test "$(git rev-parse "$REMOTE_SHA^{tree}")" = "$LOCAL_TREE"
git update-ref "refs/heads/$BRANCH" "$REMOTE_SHA" "$LOCAL_SHA"
git update-ref "refs/remotes/origin/$BRANCH" "$REMOTE_SHA"
test "$(git symbolic-ref --short HEAD)" = "$BRANCH"
test "$(git rev-parse HEAD)" = "$REMOTE_SHA"
test "$(git rev-parse HEAD^{tree})" = "$LOCAL_TREE"
S1_STATUS=$(git status --porcelain)
test -z "$S1_STATUS"
```

Record both the pre-delivery local SHA and final remote SHA/tree. The changed
tree is the task artifact; the connector-created commit remains a single-parent
non-force continuation of the same remote feature branch.

For Task 6's final readback, make the exact read-only connected-GitHub call
`github_get_pr_info(repository_full_name="lpearf-pixel/chinese-star-omen-workspace",
pr_number=54)`. Require the returned tuple to remain
`(number=54, state="open", draft=true, merged=false,
head="codex/kaiyuan-b10-calibration-v2",
head_sha="932f9e68862025bc620e0cf2d439415c5ea37af4",
base="stable/kaiyuan-v2")`; record only that tuple, not the PR body. A mismatch
is an external-state blocker, never permission to update the PR.
