# B9-PR-C RuleAssessment and Evidence Lineage Decision

## Status

```text
Task: B9-PR-C
Branch: codex/kaiyuan-b9-rule-assessment-lineage-v1
PR: #36
Base: stable/kaiyuan-v2 at 48180f6239187b491e41d9f68be0a9aab8dde95d
Evidence head before final docs: 19b320bbe0f1099a8dbe4f2c4aeefb465ab090ce
State: VERIFYING
```

## Accepted architecture

```text
AstronomyEvent/v1
→ explicit legacy matcher event projection
→ first matcher pass without external retrieval
→ candidate-only evidence hydration
→ second matcher pass
→ frozen RuleAssessment/v1
→ content-free EvidenceBundle/v1
```

The adapter reuses the existing three-valued matcher, conflict resolver, `citable-evidence/v2` resolver and two-stage retriever. It does not duplicate rule semantics or citation checks.

## Event projection

`AstronomyEvent/v1` is projected explicitly into the existing matcher shape:

- `primary_body → body`;
- `event_type → event_type`;
- `target_body_or_region → target_asterism` and singleton `related_asterisms`;
- approved angular-distance and duration measurement kinds only;
- `visible|not_visible|unknown → True|False|None`;
- persisted UTC timestamp remains explicit RFC3339 `Z`.

Unknown, duplicate or malformed measurement projections fail closed.

## Evidence hydration boundary

External retrieval is allowed only when the first matcher pass produces a `candidate_only` row. It is not called for:

- core non-matching rules;
- `partial_match` rows;
- `insufficient_data` rows;
- already citable `matched` rows.

The existing retrieval order remains authoritative:

```text
official structured recall
→ official primary evidence
→ filesystem fallback only after healthy empty official primary
```

Transport, authentication, timeout, collection and contract errors propagate. They are never converted into healthy empty evidence.

A retrieved record can become citable only when all of the following hold:

1. it is in `stage2.exact_hits`;
2. it is also present in `stage2.primary_candidates`;
3. it is a primary `fenjuan|fulltext` record;
4. explicit `match_type`, when present, is `exact_raw|exact_normalized`;
5. explicit status, when present, is official/citable/primary;
6. exactly one official/fallback provenance route is declared;
7. the existing resolver validates source, book, locator, page, paragraph, heading, anchor and hash.

Candidate overlay, structured fallback, multiple exact hits, heading-only hits, explicit candidate-only hits, missing provenance and conflicting provenance remain blocked or fail as malformed contracts.

## Public projection boundary

Only frozen public fields enter `RuleAssessment/v1`:

- event and assessment identity;
- rule-set version;
- matched rule ID/status/score;
- three-valued condition states;
- deterministic conflict summary;
- formal or provisional recommendation;
- content-free evidence references;
- narration eligibility and uncertainty reasons.

Matcher internals such as thresholds, trigger reasons, effects and source text remain available only as an in-memory diagnostic field. That field is excluded from Pydantic serialization.

A formal recommendation requires:

- matcher recommendation status `selected`;
- selected row status `matched`;
- selected row not suppressed;
- citable evidence for the same rule.

Otherwise only a provisional ID may be exposed and narration remains blocked. Manual-review conflict groups never produce a formal recommendation.

## EvidenceBundle/v1

The bundle contains no raw quote, source text, excerpt or absolute path. Each lineage entry binds:

```text
assessment_id
event_id
rule_id
evidence_id
status
claim_class = classical_quote
source_locator
content_hash
retrieval_source
resolver_status
validation_version
narration_allowed
blocking_reasons
```

Only the formally recommended citable rule has `narration_allowed=true`. Other matched, suppressed, candidate, ambiguous or missing-evidence rules remain blocked.

Canonical bundle bytes use UTF-8, sorted keys, compact separators, strict JSON and one trailing newline.

## Stable identity

Assessment, evidence, lineage and bundle IDs are deterministic SHA-256-derived stable IDs bound to their relevant public identities. Invalid rule IDs, rule-set versions and book IDs fail before external retrieval.

## Dual regression fixtures

### Evidence-rich positive path

A hermetic synthetic primary passage validates the full positive chain:

```text
石氏曰熒惑守心，天下兵起。
```

It produces a citable selected rule, eligible `RuleAssessment/v1` and content-free canonical `EvidenceBundle/v1`.

### 2026-07-21 honest blocked path

The July 21 astronomy fixture is evaluated against an empty rule set. It remains:

```text
match_status: not_matched
recommended_rule_id: null
narration_eligibility: blocked
uncertainty: no_matching_rule
```

It cannot fabricate a classical quotation or omen conclusion.

## TDD and independent review evidence

```text
Initial RED:
  3 collection errors — rule_assessment/evidence_bundle modules absent

Initial GREEN after fixtures:
  22 passed

Review RED 1:
  5 failed / 22 passed
  - unrelated-rule retrieval
  - serialization leakage
  - invalid non-matching rule ID
  - explicit non-exact hydration

Review GREEN 1:
  31 passed

Review RED 2:
  3 failed / 28 passed
  - missing retrieval provenance
  - explicit candidate-only exact hit
  - rule-set preflight ordering

Review GREEN 2:
  31 passed

Final review RED:
  4 failed / 31 passed
  - partial/insufficient external retrieval
  - conflicting provenance
  - exact hit outside primary candidate set

Final focused GREEN:
  35 passed in 1.19s

Full downstream GREEN:
  354 passed in 3.37s
```

Successful evidence-head workflows:

```text
Development Governance: 30480670491 — success
B9 RuleAssessment Lineage: 30480670199 — success
Kaiyuan Stable Core: 30480670733 — success
Kaiyuan Upstream Runtime: 30480670531 — success
```

At the evidence head, PR #36 had 21 expected files, zero review threads and zero submitted reviews.

## Explicit exclusions

B9-PR-C does not generate editorial text, Stellarium scripts, subtitles, audio, video or publishing payloads. It does not perform full-book rule structuring and does not mutate corpus, candidates, ingest, Qdrant, collections or `local_kb_default`.

## Follow-on boundary

B9-PR-D may consume only frozen `AstronomyEvent/v1`, `RuleAssessment/v1` and `EvidenceBundle/v1`. It must not read matcher diagnostics as public research facts, and may emit a `classical_quote` claim only when the corresponding lineage entry explicitly allows narration.
