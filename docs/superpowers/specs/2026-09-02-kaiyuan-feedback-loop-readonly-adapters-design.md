# Kaiyuan Feedback Loop S1 Read-only Adapters Design

**Status:** APPROVED

**Approval:** The user approved the written specification on 2026-09-02 and
authorized subsequent in-scope plans/specifications to pass without another
confirmation round.
**Approval basis:** on 2026-09-02 the user approved Solution A: consume only
local, already captured audit bundles and connect them to the existing local-KB
read-only retrieval path. Live platform access remains deferred.
**Task:** VFL-T02
**Branch:** `codex/kaiyuan-feedback-loop-readonly-adapters-v1`
**Stacked base:** `codex/kaiyuan-evidence-feedback-loop-skeleton-v1@e087d5e627bcb3e838e49015c61a3f74c0a5a2e8`
**Stable ancestry:** `stable/kaiyuan-v2@99c0a85c1f944add8d013aedbae830fe022b7c3b`

## 1. Mission and non-goals

### Mission

S1 turns a local, already captured and validated external-media audit into a
complete set of local evidence probes by using the repository's existing
read-only two-stage retrieval and citable-evidence validation paths. The probes
then enter the already completed S0 comparison, planning and atomic package
flow without a person having to hand-author retrieval results.

The primary beneficiary is the researcher-editor who needs a repeatable answer
to: “What exact local passages are worth reviewing for each audited external
claim, and what remains unresolved?” The useful real-world outcome is shorter
time from an audited media claim to a provenance-bound research package, while
the false-promotion count remains zero.

S1 succeeds when the canonical episode 22 audit and an explicit two-query plan
can produce a deterministic S0-compatible package through the read-only
adapter, with every accepted passage independently resolving as `citable`,
every relationship remaining `context_only`, and every failed retrieval aborting
before any package becomes visible.

### Unacceptable harms

- treating lexical retrieval as proof that a local passage supports or
  contradicts an external claim;
- fabricating an absent classical quotation or a 烈风/storm-system equivalence;
- accessing live Douyin or reconstructing transcript/OCR without a separate
  source-rights decision;
- writing, deleting, rebuilding or migrating any Qdrant collection, especially
  `local_kb_default`;
- leaking an API key, raw upstream body, machine path, or any source text or
  snippet newly obtained from retrieval or the resolver;
- converting authentication, timeout, contract, collection or transport errors
  into a healthy empty or unresolved result;
- changing S0, B9, B10 or evidence contract semantics in place.

### Non-goals

S1 does not scrape a platform, call a model, judge semantic support or
contradiction, train or tune retrieval, modify the corpus, create or approve a
rule, render/TTS a video, access an account, upload or publish content, complete
Reviewer B, freeze B10 thresholds, or start B10-PR-D/E/F, B11 or B12.

## 2. Stakeholders and system boundary

| Actor or external system | Role | Inputs | Outputs | Incentives or constraints |
|---|---|---|---|---|
| Researcher-editor | Selects an audited bundle and query plan; reviews results | Local paths, explicit safe collection, KB configuration | Reproducible research package | Wants useful evidence without false authority |
| Local audit store | Preserves already captured media audit bytes | `ExternalAuditBundle/v1` JSON | Strictly validated bundle | No live platform request or silent reconstruction |
| S1 adapter | Owns bounded input, retrieval orchestration and safe projection | Bundle, query plan, retriever, KB root | `LocalEvidenceProbeV1` sequence | Read-only, deterministic, fail-closed |
| Local KB Search | Executes existing two-stage retrieval | Evidence query, book, collection, limit | Structured and primary result envelopes | Retrieval only; no ingest/upsert/delete |
| Citable resolver | Revalidates exact primary hits against immutable local text | Candidate hit and explicit KB root | Precise citable or rejection status | Existing B4/D-008 authority boundary |
| S0 control plane | Compares probes and creates proposals/video request | Audit plus complete probes | Atomic feedback-loop package | Existing S0 semantics remain unchanged |
| Evidence reviewer | Determines whether a located passage is semantically relevant | Locator, hash and source context | Later reviewed assessment | S1 cannot impersonate this decision |
| B10 Reviewer B | Independent formal-rule gate | Separate B10 workbook/evidence | B10 review result | Parked as final formalization gate; unrelated to S1 completion |

Important variables are classified as follows:

- **Controlled:** query-plan schema, explicit query text, collection guard,
  result validation, citable projection, ordering, stable IDs and package
  publication.
- **Directly observed:** audit bytes and contract fields, capture rights status,
  retrieval response shape, collection/corpus provenance, resolver status,
  safe locator and evidence hash.
- **Indirectly observed:** upstream service health and the source history already
  recorded by the audit bundle.
- **Inferred:** only that a citable passage is a candidate context for human
  review. S1 makes no support, contradiction or classical-authority inference.
- **Unknown:** live platform completeness, uncaptured media, semantic
  equivalence, historical causation, model quality and publication outcome.

The external-source boundary ends at a local file. The only network-capable
boundary in S1 is the existing KB client talking to an explicitly configured
local KB Search service. Before resolving a KB credential or constructing the
retriever, the production factory must parse the effective endpoint and accept
only `http` with the literal host `127.0.0.1` or `::1`, an explicit port in
`1..65535`, no user information, query or fragment, and no path other than
empty or `/`. Hostnames such as `localhost`, non-loopback literals and redirects
are rejected. The transport must disable redirects and environment-derived
proxies; if it cannot enforce both, it fails closed instead of using another
HTTP fallback. A local-KB credential may be loaded only after this check and
may be sent only to that validated origin. No platform hostname, credential or
downloader is part of this design.

## 3. Context and feedback loop

The smallest complete S1 loop is:

```text
local audited bundle
→ strict bounded load and rights check
→ exact-coverage query plan
→ existing two-stage read-only retrieval
→ citable passage revalidation
→ context-only local probes
→ existing S0 comparison/planning/package
→ human evidence review
→ a later query/policy proposal, never an in-place mutation
```

| Transition | Expected latency | Evidence quality | Failure behavior | Owner |
|---|---:|---|---|---|
| File → validated audit | Local milliseconds | Hash- and capture-bound audit contract | Reject before retrieval | External-audit adapter |
| Plan → retrieval result | Local-service seconds | Explicit query, book, collection and corpus provenance | Typed run error; no probe batch | Local-KB adapter |
| Hit → citable reference | Local milliseconds per candidate | Full path/book/locator/page/paragraph/heading/anchor/hash validation | Omit rejected hit with safe reason counts; malformed result aborts | Citable resolver adapter |
| Probes → S0 package | Local milliseconds | Canonical S0 lifecycle and manifest hashes | Atomic no-replace failure; no partial package | S0 orchestrator |
| Package → human decision | Human timescale | Source inspection, not retrieval score | Remain unresolved | Researcher/reviewer |
| Decision → improvement | Later task | Reviewed outcome and rollback plan | Non-applying proposal only | Owning subsystem |

The S1 “intervention” is only creation of a local research package. A later
reviewer may change a new query plan or propose a policy update, but previous
audit, probe and package bytes remain immutable and independently reproducible.

## 4. Subsystems and interface contracts

### 4.1 Strict local audit adapter

The adapter accepts one explicit path and returns a defensively validated
`ExternalAuditBundleV1`. It must:

- open the path exactly once with no-follow semantics, require the opened
  descriptor to be a regular file of at most 2 MiB, and never reopen by path
  while parsing;
- take descriptor metadata before, between and after two bounded reads of the
  same descriptor; require device, inode, size and nanosecond modification time
  to remain identical and both byte snapshots to match, then hash and parse
  those frozen bytes. A path replacement therefore cannot redirect the read,
  while an in-place or metadata-preserving rewrite that changes bytes is
  rejected;
- decode strict UTF-8 JSON, rejecting duplicate keys and non-finite values;
- enforce the complete existing bundle contract and preserve canonical model
  content used by the S0 run identity;
- require every capture in the bundle to declare one of `metadata_only`,
  `quotation_for_research`, `permission_confirmed` or `public_domain`;
- reject the entire automated S1 run if any capture has
  `rights_status=unknown`, including a capture not referenced by a claim;
- require `research_only=true`, `grants_rule_authority=false` and
  `grants_classical_authority=false`;
- perform no URL fetch and add no retrieval/resolver text or machine path to
  the returned model. Existing audit fields are preserved as described in
  Section 5.

This is a replaceable filesystem adapter. A future live-source implementation
requires its own stage decision and cannot be hidden behind the same policy
version.

### 4.2 Query-plan contracts

S1 adds strict internal lifecycle contracts rather than changing
`LocalEvidenceProbeV1`:

```text
LocalEvidenceProbeRequestV1
  request_id
  source_id
  audit_id
  claim_id
  query
  kb_book_id
  query_mode = evidence
  top_k (1..20)

LocalEvidenceQueryPlanV1
  schema_version = local-evidence-query-plan/v1
  plan_id
  policy_version = vfl-readonly-probe/1.0.0
  source_id
  audit_id
  execution_scope = hermetic_test | reviewed_live
  collection
  kb_book_id
  expected_corpus_version
  requests[]

LocalKBSourceSnapshotV1
  schema_version = local-kb-source-snapshot/v1
  snapshot_id
  corpus_version
  collection
  kb_book_id
  files[] = {relative_path, size_bytes, sha256}
  tree_sha256
```

The plan must contain exactly one request for every audit claim, no extra claim,
duplicate request ID or duplicate claim ID, and it must bind the same source and
audit identities. Every request's `kb_book_id` must equal the plan-level
`kb_book_id`; S1 v1 does not span books. `collection` is mandatory: production
accepts `local_kb_kaiyuan_v2`; tests use an explicit ephemeral safe name.
`local_kb_default` is rejected before constructing a retriever call. Hermetic
tests may use `test_vfl_ephemeral_*` names only with the recording fake; the
production CLI accepts exactly `execution_scope=reviewed_live` plus
`local_kb_kaiyuan_v2` in S1. A test-only binder accepts
`execution_scope=hermetic_test` plus `test_vfl_ephemeral_*` only when handed
the concrete recording-fake type. Scope and collection cannot be crossed, and
there is no public boolean or duck-typed bypass.

Plan, snapshot and validated upstream meta share one `CorpusVersion` token.
It accepts only a real UTC producer timestamp in exact
`YYYYMMDDTHHMMSSZ` or `YYYY-MM-DDTHHMMSSZ` form and validates calendar/time
fields by strict parse plus round trip. Control/whitespace characters, `=`,
slashes, backslashes and all descriptive or path-like versions are rejected
before retrieval. This makes the value safe for its fixed `key=value` note
without escaping or leaking caller text.

The adapter does not derive queries from claim prose. Query changes are explicit
versioned research inputs, so a changed query produces a changed plan and run
identity rather than silently rewriting history.

The query-plan file uses the same strict UTF-8, duplicate-key, non-finite-value,
descriptor-stable double-read policy as the audit adapter, with a 256 KiB size
limit. Before Pydantic validation, every parsed JSON graph is iteratively
bounded to depth 64 and 100,000 total mapping/list/scalar nodes; JSON decoder
`RecursionError` and budget overflow map to the same fixed typed local-input
failure. Its canonical model bytes are hashed before any retrieval call. The
canonical plan SHA-256, fixed adapter policy version, plan and request IDs,
query, `top_k`, collection, expected and observed corpus versions, response
schema versions, any source-snapshot SHA-256 used for local file access and the
projected reference set are all bound into the emitted probe provenance. Exact
replay must therefore reproduce those values or yield a different probe and S0
run identity.

`LocalKBSourceSnapshotV1` is a caller-supplied, read-only attestation for the
specific KB root; S1 never creates or edits it. It uses the same strict bounded
descriptor read as the query plan and is at most 256 KiB. Its files are the
exact sorted inventory of regular, non-symlink `fenjuan|fulltext` files eligible
to the existing scanner under the root. Relative paths must be unique,
canonical and confined; sizes and lowercase 64-hex SHA-256 values over raw file
bytes are mandatory.
`tree_sha256` is the SHA-256 of canonical sorted-key JSON for the complete
`files` array. Collection,
`kb_book_id` and corpus version must equal the plan-level values. The Episode 22
plan fixes `kb_book_id=kaiyuan_zhanjing` for both requests.

Before retrieval, S1 recomputes the eligible path inventory and every file hash
and requires exact equality, with at most 64 MiB per file and 512 MiB across the
snapshot; it repeats the tree check after the batch. More importantly, all
production local file reads go through an S1-owned snapshot accessor. It holds
one root directory descriptor for the batch and opens canonical relative paths
with beneath/no-symlink-component semantics. For each access it verifies
descriptor identity, regular-file type, size and raw-byte SHA-256 against the
manifest, then gives the scanner or resolver only the immutable bytes read from
that same descriptor. The consumer never reopens the pathname or uses the
existing path-keyed passage cache. In strict S1 mode the scanner obtains its
complete ordered inventory from the accessor's immutable snapshot-file tuple
and attempts every exact manifest path; it never `rglob`s or otherwise
enumerates the live root. A manifest file removed during its turn therefore
fails its exact load even if restored before postflight, rather than silently
disappearing from results under the same identity. Existing scanner and
resolver semantics gain additive inventory/byte-loader seams for this
accessor; their default callers remain unchanged.

The resolver's legacy entry point currently consults global settings even when
the root is explicit. S1 additionally supplies a narrow immutable resolver
context containing only source-root and ingest-source labels. With explicit
root, snapshot loader and context, the resolver neither calls global
`get_settings()` nor re-resolves configuration; the production factory derives
the context from its one isolated settings copy and hermetic tests provide a
fixed test context. Snapshot bytes are held only in memory for the batch and
are never logged or persisted. Replace-and-restore, symlink, in-place rewrite,
missing manifest-path load and hash mismatch all abort.

The canonical snapshot-manifest SHA-256 is safe provenance and enters every
probe preimage. Missing, stale, incomplete or changing snapshot evidence aborts
before any package is published. Hermetic tests create temporary hash-only
snapshot manifests; no snapshot fixture or raw corpus byte is added to the
repository. A real smoke requires a separately supplied reviewed live plan and
matching manifest and is `BLOCKED`, not passed, when either is absent.

### 4.3 Read-only retriever protocol

The adapter depends on a narrow protocol exposing only:

```python
def two_stage_retrieve(query: str, **kwargs: object) -> Mapping[str, object]: ...
```

Production uses the existing `KBSearchRetriever`; tests use a recording fake.
The adapter calls only `two_stage_retrieve` with explicit `query_mode=evidence`,
`filters={"kb_book_id": request.kb_book_id}`, collection and bounded `top_k`.
It never calls meta mutation, ingest, upsert, delete, promote or candidate-sync
operations.

Production construction is part of the safety boundary. The production-only
factory itself accepts exactly
`collection=local_kb_kaiyuan_v2`; it rejects `local_kb_default`, hermetic
ephemeral names and every other collection before config, endpoint, transport,
meta, credential or retriever work, even if called without the CLI binder.
After the loopback endpoint check, the factory uses the same pinned,
proxy-free, redirect-free
transport to read `/v1/meta` without a credential. It strictly requires
`meta_status=ok`, `schema_version=corpus-manifest/v1`, the plan collection and
expected corpus version, a non-empty ingest run ID and created-at string, and a
lowercase `sha256:<64 hex>` source-manifest hash. The canonical validated meta
shape accepts the two exact repository-produced variants: the corpus-manifest
script adds string-list `source_roots` and `excluded_roots`; the normal ingest
writer instead adds `managed_by="local-kb-unified/v2"`,
`collection_schema="passage-v2"` and a closed `run_stats` object containing
non-negative strict integers for `desired`, `new`, `changed`, `unchanged`,
`stale`, `upserted`, `deleted`, `errors` and `elapsed_ms`. The base fields alone
are also valid because they are the public `/v1/meta` minimum. Mixing variants,
partial variants, all other unknown fields, wrong types and non-finite values
fail closed. The complete validated object, including the exact accepted
variant and all `run_stats`, is canonicalized into an in-memory
`session_meta_sha256`. That digest is used only to detect any before/after
session drift, including a change to `elapsed_ms`; it is never persisted in a
probe, package, identifier or note. A second canonical semantic projection
contains exactly `schema_version`, `corpus_version`, `ingest_run_id`,
`source_manifest_hash`, `collection`, `created_at`, and the exact key
`producer_variant`. Its value is `base`, `corpus_manifest_script` or
`normal_ingest`. `base` adds no extension fields;
`corpus_manifest_script` adds `source_roots` plus `excluded_roots`; and
`normal_ingest` adds `managed_by` plus `collection_schema`. It excludes `meta_status` and the
entire operational `run_stats` object. Its SHA-256 is `provenance_sha256` and
is the only meta-derived digest allowed in persisted identity. Thus an
in-session latency change still aborts, while two fresh sessions differing
only in run telemetry have the same persisted provenance; a change to any
semantic projection field changes persisted identity. Both digests become
part of `VerifiedUpstreamProvenanceV1`. Only after that succeeds may the
factory resolve a credential and create an isolated
settings copy that pins `kb_sources_root` to the validated explicit KB root,
disables the additional Obsidian root, disables candidate overlay, and pins the
retriever's default collection to the validated plan collection. It also
derives the narrow resolver context from that same copy, and the returned
pinned session exposes only that immutable context rather than global settings.
The validated
root must be a real directory; all fallback paths must remain within it. The
original global settings object is not mutated. Tests must prove that an
invalid endpoint or invalid/mismatched meta response is rejected before
credential resolution or retrieval and that neither a key, endpoint user
information nor raw meta body appears in errors. S1 uses the injected strict
transport seam for all meta and retrieval calls; it does not fall back to the
current `urllib` transport path.

S1 resolves configuration once per factory call: an explicit internal
`config_path` wins, then a non-empty `APP_CONFIG_PATH`, otherwise the default is
the module-derived absolute `apps/star-omen/config/config.yaml`, independent of
the current working directory. The same resolved `Path` is passed to both the
endpoint-only loader and the later fresh `load_settings`; they may not perform
separate relative-path resolution.

The pinned transport streams both response bodies before shape validation. It
accepts only `GET /v1/meta` with no JSON payload/auth headers and
`POST /v1/retrieve` with a mapping payload and the explicit credential headers;
accepts only absent/identity content encoding and a JSON media type, enforces a
256 KiB decoded-byte limit for `/v1/meta` and 4 MiB for `/v1/retrieve`, decodes
strict UTF-8, rejects duplicate object keys and `NaN`/`Infinity`, applies the
same depth/node budgets as local JSON, and requires a root mapping. It rejects
an excessive `Content-Length` before iteration and stops as soon as streamed
decoded bytes exceed the path-specific limit. No ordinary `response.json()` or
already-parsed mapping may bypass this raw-body boundary.

The deployed `/v1/retrieve` response schema does not itself carry a corpus
version. S1 therefore does not invent one or require an unavailable response
field. Its raw-response validator first enforces every field the deployed
response does own (schema, mode, stage, card pool, collection, filters, counts,
finite hits and bounded arrays). For a primary-stage response, raw `hits` must
either be exactly empty or every hit must explicitly carry a non-null
`card_type` from the requested primary card pool; missing, null or other card
types are response errors before normalization and before fallback. Therefore
`official_primary_empty` can only derive from a validated raw empty list, never
from filtering a non-empty malformed list. If a future response supplies a corpus field,
it must equal the verified meta value. Only after raw validation succeeds, a
keyword-only S1 provenance seam annotates the retriever's internal normalized
stage/observability dictionaries with the separately verified corpus version,
semantic provenance SHA-256 and provenance source `upstream_meta`. The
session-meta digest never leaves the pinned session. The two-stage validator
requires those exact annotations and never represents them as response-native.
A narrow `PinnedReadOnlyKBSession` re-fetches and strictly compares `/v1/meta`
immediately before and after every `two_stage_retrieve` call. Any observed meta
drift aborts the whole batch. An injected S1-only provenance guard also performs
the same comparison immediately before and in `finally` after each actual
official `/v1/retrieve` request, so stage-1/stage-2 drift cannot pass merely by
restoring meta before the outer postflight. The limitation that an external
service could change and restore state entirely between adjacent observations
is recorded rather than claimed away.

The source-snapshot accessor is also injected as the retriever's fallback
guard: it must pass before `_scan_primary_files` may consume a file, and the
fallback scanner parses only accessor-returned immutable bytes. The same
accessor supplies any file later parsed by the citable resolver. Without it,
production filesystem fallback or resolution fails with a typed safe provenance
error; official retrieval alone cannot attest the bytes under the local KB
root.

For every response the adapter requires a mapping with complete `stage1`,
`stage2` and observability shapes. It requires:

- `stage1` schema `kb-retrieve/v2`, mode `evidence`, stage
  `structured_recall`, card types exactly
  `[zhusu_card, term_card, extract_card]`, the requested collection and exact
  `kb_book_id` filter;
- `stage2` schema `kb-two-stage/v2`, mode `evidence`, stage
  `primary_evidence`, card types exactly `[fenjuan, fulltext]`, and an
  `official_result` with schema `kb-retrieve/v2`, the same collection/filter,
  mode, stage and card pool;
- every bounded result list (`hits`, `exact_hits`, `related_hits`,
  `primary_candidates`, `candidate_overlay_hits` and `structured_fallbacks`)
  to contain no more than the requested `top_k`; and
- top-level observability schema `kb-observability/v1`, operation
  `two_stage_retrieve`, empty `provenance_conflicts`, and collection/corpus
  provenance present and equal to the plan's collection and expected corpus
  version, with the exact preflight semantic provenance SHA-256 and provenance source
  `upstream_meta`.

The semantic provenance SHA requirement applies identically to
`stage1.observability`, `stage2.official_result.observability` and the outer
observability object. The SHA is exactly 64 lowercase hexadecimal characters;
missing or differing values abort before projection.

Omission is a contract error rather than permission to infer a value. The
adapter also rejects conflicting official/fallback provenance, non-list hit
fields, an exact hit absent from the primary candidate set, a non-primary card,
candidate/overlay status presented as official, collection mismatch,
corpus-version conflict, or any candidate-overlay rows.

Filesystem fallback is allowed only after a valid, healthy official primary
response reports an empty primary result and stage 2 reports
`official_primary_empty=true`, `fallback_used=true` and
`fallback_reason=official_primary_empty`. It uses only the pinned KB root. A
transport, authentication, timeout, collection or response-contract error
aborts before fallback. Existing typed `KBSearchError` values propagate as run
errors; their raw details are not copied to output.

An exact hit's explicit status may only be absent or one of `official`,
`citable` and `primary`. Candidate-only, stale, pending, ambiguous or unknown
statuses never reach the resolver. A supplied `match_type` must be `exact_raw`
or `exact_normalized`. An absent `match_type` is accepted only for an
official-primary hit that is deeply equal as a parsed JSON mapping in both
`stage2.official_result.exact_hits` and `stage2.primary_candidates`, with
`official_primary_used=true` and `fallback_used=false`. A fallback hit must
declare `exact_raw` or `exact_normalized`; no missing or other match type reaches
the resolver. Hit mappings must contain only finite JSON values; deep equality
is equivalently equality of their strict canonical sorted-key JSON encodings,
not unavailable upstream response bytes.

After the complete envelope and hit checks pass, the validator canonicalizes
every `stage2.exact_hits` mapping as strict sorted-key compact JSON bytes,
removes only byte-identical mappings and sorts the remaining mappings by those
bytes. Each item is retained only as an immutable canonical-byte wrapper; the
projector decodes a fresh mapping and never retains or exposes a caller-owned
mutable alias. That unique sorted tuple is the validated exact-hit tuple, and
`exact_candidate_count` is its length. Consequently hit permutation and an
identical duplicate cannot alter notes, probe identity or S0 run identity.
Distinct mappings still count as distinct exact candidates even when the
projection below resolves them to the same passage; passage-reference
deduplication is intentionally a later, separate operation.

### 4.4 Citable projection

Only `stage2.exact_hits` with `fenjuan|fulltext` card types are considered. A
new allowlisted hit-to-resolver projection is normative; the more permissive
rule-assessment helper is not reused implicitly. It applies these rules:

- take a path only from `relative_path`, `source_path` or `path`; reject when
  none is present or when multiple non-empty aliases resolve to different
  files;
- convert an absolute path to a relative path only when its resolved target is
  inside the validated KB root; require relative paths to be canonical and
  confined, and never guess a path;
- require the candidate book ID to equal the request book ID, require a
  non-empty `page_marker`, and accept `heading_path` only as a list of strings
  and `paragraph_index` only as a non-negative integer when supplied;
- take an optional claimed locator only from `source_locator` or `locator`,
  rejecting conflicting non-empty aliases, so the resolver can validate it
  against the path and page rather than trusting it;
- take an explicitly supplied anchor only from `anchor_text`, `raw_text`,
  `quote` or `excerpt`, rejecting conflicting non-empty aliases and never using
  `snippet` as a fallback. Because the deployed official response exposes only
  a truncated `snippet`, an official primary hit with no allowed anchor may be
  rehydrated only from the snapshot accessor when it supplies canonical
  `raw_start` and `raw_end` integer offsets: parse the verified immutable source
  bytes, require exactly one passage with those exact boundaries, require every
  supplied locator/page/paragraph/heading field to match that passage and every
  hash to satisfy the field-specific resolver semantics below, and
  use that passage's exact raw text as the in-memory resolver anchor. Missing,
  invalid or non-unique boundaries reject the candidate; the snippet is never
  compared, promoted or persisted; and
- pass through only `content_hash`, `raw_content_hash` and
  `normalized_content_hash` under their original meanings; require every
  supplied value to match `^sha256:[0-9a-f]{64}$` and at least one to be
  present, with no hash inference or field substitution before resolution.
  The resolver's established semantics remain exact:
  `raw_content_hash` matches passage raw content,
  `normalized_content_hash` matches passage normalized content, and
  `content_hash` may match either the exact in-memory anchor hash or the
  passage raw-content hash. Those three values need not be mutually equal.

Every projected candidate is passed through the existing `resolve_evidence`
validation path with the explicit KB root and snapshot accessor; it parses the
accessor's already verified immutable bytes and may not reopen the path.
Resolver output must contain a canonical source locator, page marker,
non-negative paragraph index, heading path and a
`raw_content_hash` matching `^sha256:[0-9a-f]{64}$`. Only `status=citable`
becomes a `LocalEvidenceReferenceV1`:

- `evidence_class=citable_passage`;
- `relationship=context_only`;
- locator is exactly
  `kaiyuan-passage:v1:<source>:<page>:p<paragraph>`, where source and page are
  UTF-8 percent-encoded per RFC 3986 with only unreserved characters left
  literal and uppercase `%HH`, and paragraph is canonical unsigned decimal;
- SHA-256 is the validated passage raw-content digest normalized from the
  resolver's `raw_content_hash` field only, stripping the required
  `sha256:` prefix to the contract's exact 64-lowercase-hex form; the resolver's
  `content_hash` is never substituted;
- stable reference ID is derived from claim, locator and evidence hash;
- note is the exact literal
  `Semantic support or contradiction remains unreviewed.`.

Raw retrieval/resolver source text, snippet, absolute path, retrieval score and
upstream body are not persisted. Identical
`(claim_id, locator, evidence_sha256)` tuples are deduplicated. References are
sorted by
`(evidence_locator, evidence_sha256, evidence_ref_id)`. One whole-batch registry
maps each reference ID to its complete `(claim_id, locator, evidence_sha256)`
tuple; a different tuple aborts both within one claim and across claims. The persisted `citable_count` is exactly
the length of this final deduplicated, sorted reference tuple, not the number of
resolver calls or pre-dedup citable results. Thus two distinct exact-hit
mappings may contribute two exact candidates yet one citable reference.

Rejected candidates never become evidence references. Only aggregate counts for
the exact resolver status allowlist `candidate_only`, `source_outside_root`,
`missing_source`, `book_mismatch`, `card_type_mismatch`, `locator_mismatch`,
`page_mismatch`, `paragraph_mismatch`, `heading_mismatch`, `anchor_mismatch`
and `hash_mismatch` may enter deterministic notes; no candidate-level
diagnostic is persisted. An unknown resolver status aborts the batch.

Projection has three non-overlapping failure classes. A malformed raw or
two-stage envelope, provenance mismatch, snapshot/accessor integrity exception,
unknown or malformed resolver result, inconsistent `citable` result, or
reference-ID collision aborts the current claim and therefore the whole batch.
A hit that passes the envelope but cannot form a safe resolver candidate due to
missing/conflicting projection aliases, invalid/ambiguous offsets or another
candidate-local allowlist defect is omitted without a resolver call, reference,
resolver-status counter or candidate diagnostic; it still contributes to the
already-fixed `exact_candidate_count`. A well-formed resolver result with one of the
exact known non-citable statuses is omitted and increments only that aggregate
status count. These classes cannot be silently promoted or collapsed.

The adapter always emits `result_state=unresolved`, whether it finds zero or
more citable context references. It never emits `corroborated` or
`contradicted`. `not_searched` remains available to S0 callers but is not an
output of a successfully executed S1 plan.

S1 binds provenance without changing `LocalEvidenceProbeV1`:

- `probe_id` is a stable hash identity over adapter policy version, canonical
  plan SHA-256, plan ID, execution scope, request ID, source, claim, query, `top_k`, collection,
  expected and observed corpus versions, verified upstream semantic
  provenance SHA-256 and provenance marker, any local source-snapshot
  SHA-256, response schemas and projected references;
- `retrieval_version` is the bounded string
  `vfl-readonly-probe/1.0.0:sha256:<64 lowercase hex>`. Its digest commits to
  canonical sorted-key JSON containing the fixed adapter policy, canonical
  query-plan SHA-256, verified upstream semantic provenance SHA-256/source, local
  source-snapshot SHA-256 and validated response schema versions; this keeps
  the existing S0 field within its 256-character contract without dropping
  provenance;
- deterministic allowlisted notes record plan ID, request ID, collection,
  expected/observed corpus versions, verified upstream semantic provenance
  SHA-256/source, `top_k`, validated unique exact-candidate count, citable count,
  source-snapshot SHA-256 when used and per-status rejection counts.

The validated response-schema tuple is exactly
`("kb-retrieve/v2", "kb-two-stage/v2", "kb-retrieve/v2")` in
stage-1/wrapper/nested-official order. It is never deduplicated or derived from
hit/input ordering.

Because the complete probe object is already part of the S0 run preimage, a
plan, collection, corpus version, response schema or projected-evidence change
therefore changes the run identity. Notes contain no text, paths, scores,
latency, secrets or raw error details.

### 4.5 Batch adapter and S1 CLI

The batch adapter validates all inputs first, executes requests in canonical
claim order, accumulates probes only in memory and returns a complete tuple only
after every request succeeds. Any error discards the in-memory partial batch.

The S1 CLI accepts explicit audit, query-plan, KB-root, source-snapshot and
output paths. The safe collection and expected corpus version come only from
the validated plan; the snapshot must agree rather than override them. Endpoint
and key configuration use the constrained factory in Section 4.3. The CLI
generates probes, calls the unchanged S0 build API and invokes S0 atomic
no-replace publication only after the complete batch is valid. It prints a safe
actionable error and exits nonzero on failure. Its non-abbreviating argument
parser overrides every parse-error path so unknown options, missing values and
unexpected positionals produce only the fixed typed code and never echo argv;
the outer exception boundary includes parsing itself.

The first production CLI is deliberately episode-22-only because the unchanged
S0 planner currently expects that pilot's two-claim shape. It requires source
`media:douyin:zushan:collection-7664842437629921326:episode-22`, audit
`audit:douyin:zushan:episode-22` and work `7669807398794598565`. The adapters
remain reusable at their internal contracts, but dispatching another audit is a
later policy/version decision rather than an accidental side effect of this
pilot CLI.

The committed episode-22 query-plan asset is explicitly
`execution_scope=hermetic_test`, uses a `test_vfl_ephemeral_*` collection and
is not an attestation of the live release manifest. It uses the normal-ingest
producer's timestamp grammar and is paired only with recording meta and a
temporary matching snapshot through the test-only binder. The public CLI must
reject this fixture before credential or retrieval access. An opt-in real smoke must instead use
a separately caller-supplied, reviewed query plan whose exact corpus version
matches both the caller snapshot and the currently served immutable release
manifest. The CLI never copies or guesses that value from live meta. Absence of
this live plan is a `BLOCKED` smoke precondition, not permission to treat the
hermetic fixture as production evidence.

Production `main` has no retriever-injection argument: it always applies the
reviewed-live binder and constructs the pinned production session before
calling a shared complete-batch/build/publish core. Hermetic E2E reaches that
same core only through a helper defined in the test module that requires the
concrete recording-retriever type and hermetic/ephemeral binder. Tests never
monkeypatch the production binder or factory, and public CLI invocation of the
committed fixture fails before credential or network access.

A mandatory hermetic production-wiring E2E uses a reviewed-live temporary plan
and snapshot, invokes the real root Make target/public CLI from repository root,
uses the real production binder, factory, pinned HTTP transport, retriever,
projector and publisher, and binds only a test-owned `127.0.0.1` random-port
HTTP server that emits strict deployed-shape meta/retrieve bytes. It does not
inject or monkeypatch a retriever, binder or factory. This proves the public
assembly and CWD-independent default config path while remaining distinct from
the optional real Local-KB smoke.

### 4.6 Compatibility and replacement boundaries

| Subsystem | Input contract | Output contract | Failure behavior | Replaceable without changing consumers |
|---|---|---|---|---|
| Audit file adapter | Local path | `ExternalAuditBundleV1` | Reject before retrieval | Yes, with same rights/validation policy |
| Query plan | `LocalEvidenceQueryPlanV1` | Exact single-book claim requests | Contract rejection | Yes, by a new explicit version |
| Source snapshot | Explicit manifest + KB root | Verified immutable file bytes | Abort before local parsing | Yes, by the same accessor contract |
| KB adapter | Plan + read-only retriever + KB root | Complete probe tuple | Typed batch abort | Yes, protocol-bound |
| Citable projection | Exact primary candidate | Context-only evidence ref | Reject candidate or abort malformed response | Yes, while D-008 remains authoritative |
| S0 orchestration | Audit + probes | Existing feedback-loop package | Atomic no-replace | Unchanged by S1 |

S1 does not modify frozen B9 contracts, existing external-media public schemas
or S0 package semantics. New contracts are additive and internal to the
feedback-loop adapter boundary.

## 5. Observation–hypothesis–decision model

The system keeps these layers separate:

- **Observation:** exact audit claim, explicit query, observed collection/corpus
  version, citable validation result and safe locator/hash.
- **Hypothesis:** a citable passage may be relevant context for the external
  claim; the relationship remains unclassified.
- **Decision:** S0 keeps publication and cross-module application blocked;
  semantic acceptance requires a later human-reviewed artifact.
- **Outcome:** optional later human/publication facts remain caller-supplied S0
  outcomes and do not edit S1 probes.
- **Proposal:** S0 may suggest a retrieval, corpus-research, semantic-policy or
  editorial improvement, always with `apply_allowed=false`.

Retrieval rank, lexical overlap and a `citable` status prove retrievability and
source identity, not semantic agreement. A future reviewed or model-assisted
semantic stage must create a new linked object with supporting and contradicting
evidence, confidence, verification method and reviewer state. It may not mutate
an S1 probe in place.

The unchanged S0 package intentionally retains the already approved audit
contract's short `exact_text`, public source/capture locators, fixed URL and
creator account locator, plus the explicit query text required for replay.
Those fields are research-only local package data and inherit the audit store's
access and retention boundary; S1 does not claim to redact them. Its privacy
guarantee is narrower and testable: it adds no retrieval response body,
retrieval/resolver source text or snippet, absolute filesystem path, score,
latency, credential or raw error detail to probes, notes, manifests, stdout or
stderr.

## 6. Minimum closed-loop pilot

- **Narrow domain:** 祖山觀 episode 22 / work `7669807398794598565`.
- **Target environment:** hermetic recording retriever for mandatory tests;
  configured local KB Search plus `local_kb_kaiyuan_v2` for an opt-in read-only
  smoke, with a separately reviewed live query plan and matching caller-supplied
  local source-snapshot manifest before filesystem fallback or resolver access.
- **Entry condition:** the committed audit passes strict local/rights checks;
  the plan covers its two claims exactly; S0 head is the stacked ancestor.
- **Queries:** `毕宿 烈风 古典原文 来源` and
  `烈风 海上风暴 古典对应关系`, each explicitly bound to one claim.
- **Evidence collected:** only citable exact passage locator/hash references;
  WMO remains external `modern_authority/context_only`.
- **State estimated:** both local probe states remain `unresolved`; zero or more
  context-only citable references may be attached.
- **Intervention:** atomically create one S0-compatible local package with a
  blocked manual-publication handoff.
- **Immediate validation:** deterministic bytes, complete query coverage,
  citable replay, no mutation calls and no partial output on injected errors.
- **Delayed validation:** a researcher can relocate each reference and record
  whether it was actually useful; that result informs a later plan/proposal,
  not the current evidence status.
- **Human review point:** before any semantic support/contradiction state,
  classical claim, formal rule or publication.
- **Stop rule:** any rights, identity, provenance, contract, transport,
  collection, corpus-version, local source-snapshot or citable-validation
  integrity failure stops the run. A healthy empty result is valid but
  unresolved only when any attempted filesystem fallback was snapshot-bound.

The hermetic pilot is the required implementation gate because it proves every
success and failure path without touching a service. The real local-KB smoke is
reported separately as `PASSED`, `NOT RUN` or `BLOCKED`; absence of that
environment cannot be misstated as passed and must be satisfied before an S2
model consumes real S1 output.

## 7. Metrics and validation

### Component health

- audit/plan validation result;
- request count and exact claim coverage;
- healthy empty, exact candidate, citable reference and rejected-reason counts;
- typed failure code and failed claim ID, without raw error details;
- observed collection and corpus version;
- local source-snapshot manifest and tree SHA-256 when filesystem bytes are
  used;
- deterministic probe/package hashes;
- retriever call log proving only the allowed method and arguments.

Latency may be emitted to operator logs but cannot enter canonical probe or run
identity.

### Decision quality

- automatic decisive classifications: exactly zero;
- false classical promotions: exactly zero;
- percentage of citable references later judged useful by a human;
- query revisions and reversals, preserved as new versioned plans;
- disagreement between retrieval candidates and human evidence review.

### System outcome and learning

- time from audited claim to reviewable local evidence context;
- percentage of audit claims with a complete, reproducible probe;
- time to identify and correct a failed query or schema drift;
- audit completeness and rollback/replay success;
- researcher burden and later proposal acceptance.

Engagement or publication metrics never serve as classical truth labels.

## 8. Human review and escalation

- Any move from `unresolved/context_only` to `corroborated` or `contradicted`
  requires a separately designed reviewed semantic artifact.
- Conflicting passages, multiple plausible locators, textual variants or
  uncertain subject/boundary readings escalate to research rather than score
  arbitration.
- Any future model output is candidate-only and cannot approve its own
  classification.
- Publication remains behind the existing B9 machine, AI and human gates plus
  the S0 manual handoff.
- B10 Reviewer B remains a different independent human and is still required
  for threshold freeze and formal B10/B11 rule release. It is deliberately
  parked as that terminal formalization gate and does not block VFL-T02.
- Any later S2 reviewed-semantic design must make reviewer actions and
  reversals append-only and hash-bound; S1 only preserves immutable probes,
  audits and packages and does not define that future review artifact.

## 9. Risks, unknowns and reversible decisions

| Assumption or risk | Evidence today | Consequence if wrong | Test | Reversible response |
|---|---|---|---|---|
| Exact lexical hit is semantically relevant | Retrieval and citable validation prove identity only | False support claim | Assert every S1 relationship is `context_only` | Keep unresolved; revise query or add later human review |
| Retrieval response schema remains stable | Existing client and tests use v2 envelopes | Silent misprojection | Adversarial malformed/conflicting response matrix | Fail closed; update adapter under a new policy version |
| Collection is safely configured | Existing defaults exist, including protected legacy state | Accidental protected access | Require explicit safe collection; reject `local_kb_default` before call | Change operator input; no state rollback needed |
| KB endpoint is truly local | Existing settings can contain an arbitrary base URL | Credential or query sent off-host | Literal-loopback parser tests, credential-provider spy and redirect rejection | Abort before key resolution/request; correct local settings |
| Filesystem fallback stays in scope | Existing retriever can scan configured roots and candidate overlay | Read outside the approved corpus | Pinned-root, disabled-overlay and path-confinement tests | Abort; rebuild isolated settings without mutating globals |
| Local resolver/fallback bytes match the named corpus | Official observability describes service state, not the local KB root | Package cites bytes from a different snapshot | Exact pre/post source-snapshot inventory and content-hash verification | Abort; obtain a matching read-only manifest or do not use local files |
| Corpus provenance is consistent | Two-stage observability exposes collection/version conflicts | Evidence bound to wrong snapshot | Missing/conflicting/mismatched version tests | Abort and rerun after service correction |
| Local audit rights declarations are usable | Current episode 22 is metadata-only research capture | Unauthorized automation | Rights-status allowlist and unknown-rights rejection | Keep file manual-only; no platform access |
| File remains stable during read | Local files can be replaced, rewritten or symlinked | TOCTOU/tamper | Symlink, oversize, path-replace, in-place and metadata-preserving rewrite tests | Reject and retry from a stable file |
| Safe projection omits newly obtained sensitive data | Existing hits may carry text/path/raw errors while S0 retains audit fields | Secret/content leakage | Field-aware package/stdout/stderr scans that allow only documented audit/query fields | Reduce allowlist; old package remains immutable |
| Retrieval is deterministic enough for canonical output | Hits may arrive reordered | Run drift | Permutation and duplicate tests | Canonical sort/dedup or fail on conflicting identity |
| Stacked delivery remains auditable | S0 is pushed but not integrated to stable | Unclear merge topology | Exact ancestry and changed-path checks | Keep S1 on a separate stacked branch; never push stable |

All S1 decisions are reversible by disabling the adapter or reverting the
stacked branch. There is no database, corpus, rule, account or external-source
migration to roll back.

## 10. Stage gates and entry criteria

| Stage | Scope | Required evidence to enter | Required evidence to exit | Forbidden expansion |
|---|---|---|---|---|
| S1-A | Strict audit/query-plan contracts | Approved Solution A and clean `e087d5e` base | RED/GREEN contract, rights and collection-guard tests | No retriever or platform side effect |
| S1-B | Read-only KB-to-probe adapter | S1-A green | Response/error/citable matrices; deterministic complete batch; no-mutation proof | No decisive semantic classification |
| S1-C | Episode 22 CLI and S0 integration | S1-B green | Hermetic E2E, atomic collision/error tests, regressions and review | No render, model, upload or publication |
| S1 exit | Reviewed stacked feature candidate | Focused and related gates green | Independent code/governance review (not B10 Reviewer B), full downstream, governance, compile/diff/scope/secret scans, exact SHA/tree and remote readback | No B10 artifact, stable/main or PR #54 change |
| S2 | Optional local-model semantic candidates | Separate accepted design; real local-KB S1 smoke recorded successful | Candidate-only evaluation, calibration, human review and rollback evidence | No model approval or automatic application |
| S3 | B9 media/TTS plus manual publication | Separate media design and real-device evidence | Existing B9 hard gates plus explicit human review | No automatic account publication |
| S4 | Bounded upload assistance | Separate credential/security/revocation decision | Account-specific safety and rollback evidence | No unattended publishing |
| B10 terminal gate | Threshold freeze and formal rule path | Independent Reviewer B and all frozen B10 gates | Approved canonical freeze/release evidence | Cannot be substituted by S1/S2/media output |

Calendar progress alone cannot advance a stage. Missing local-service evidence
is recorded accurately but does not prevent completion of unrelated hermetic
implementation work.

## Task contract

### Current state

- Repository: `lpearf-pixel/chinese-star-omen-workspace`; commands resolve the
  active worktree with `git rev-parse --show-toplevel` rather than recording a
  machine-specific absolute path.
- Branch: `codex/kaiyuan-feedback-loop-readonly-adapters-v1`.
- Base HEAD: `e087d5e627bcb3e838e49015c61a3f74c0a5a2e8`.
- Working tree at task start: clean.
- Live stable: `99c0a85c1f944add8d013aedbae830fe022b7c3b`.
- Live open PR set at task start: Draft #54 only, human-review blocked.

### Goal

Produce one deterministic, complete set of context-only local evidence probes
from the local episode 22 audit and explicit query plan through the existing
read-only KB and citable resolver paths, then build the unchanged S0 package.

### Allowed scope

- additive code/tests under `apps/star-omen` for feedback-loop S1 adapters and
  CLI;
- one canonical episode 22 query-plan fixture and its manifest update;
- a discoverable Make entry point using literal-safe argument handling;
- VFL-T02 task, decision, memory, work-log, plan and summary documentation.

### Prohibited changes

- raw corpus, B9/external-media/S0 public semantic changes;
- `apps/local-kb-unified`, Qdrant configuration or any ingest/mutation call;
- any read, write, delete, rebuild or migration of `local_kb_default`;
- live platform access, transcript/OCR reconstruction, model calls, rendering,
  TTS, platform/account credentials, uploads or publishing; a local-KB API key
  is allowed only after literal-loopback validation through Section 4.3 and
  must never enter output or errors;
- PR #54, Reviewer A/B artifacts, threshold freeze, B10-PR-D/E/F, B11/B12;
- direct stable writes, `main`, force push, merge or Runner dispatch.

### Done

- exact query-plan coverage and safe collection/corpus binding are enforced;
- literal-loopback transport and local source-snapshot binding are enforced;
- strict local audit loading and rights policy are enforced;
- only revalidated citable exact hits become context-only references;
- all successful S1 probes remain unresolved and S0 compatible;
- typed retrieval failures produce no probes/package/partial destination;
- no-mutation, determinism, atomicity, privacy and episode 22 tests pass;
- task state, decision, verification and remaining environment evidence are
  recorded accurately; independent review has no unresolved Critical or
  Important finding.

### Verify

The implementation plan must provide exact commands for:

```text
focused S1 contract/adapter/CLI tests
loopback transport, redirect/proxy and source-snapshot adversarial tests
feedback-loop + external-media + retrieval + citable-resolver regressions
complete apps/star-omen downstream tests
root governance unit and development-governance checks
compileall, git diff --check and exact changed-path audit
forbidden collection/mutation/platform/secret/machine-path scans
two deterministic episode 22 builds and occupied-output replay
```

The real local-KB smoke is reported separately and never fabricated when its
reviewed live plan, matching snapshot, service or configuration is unavailable.

### Delivery

- use small auditable commits on the stacked S1 feature branch;
- after complete local verification and review, non-force push only
  `codex/kaiyuan-feedback-loop-readonly-adapters-v1` when authorized;
- do not change the existing S0 remote ref, stable, `main` or PR #54;
- do not create a VFL PR until its base topology is explicitly selected;
- Runner remains `NOT RUN` for this routine feature task.

## Considered alternatives

1. **Selected — context-only read-through adapter.** It connects real
   retrieval while preserving the boundary between retrievability and semantic
   truth. It is the smallest useful S1 and leaves semantic classification to a
   separately reviewed stage.
2. **Rejected for S1 — deterministic lexical support/contradiction rules.** A
   phrase match cannot reliably establish subject, scope, polarity, textual
   variant or historical equivalence. This would create a new semantic policy
   without calibration.
3. **Deferred to S2 — model-assisted semantic classification.** A local model
   may later propose relationships, but it needs candidate-only contracts,
   evaluation, human review and rollback. Including it now would collapse two
   independent stage gates.
