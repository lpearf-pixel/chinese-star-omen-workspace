# Kaiyuan Legacy PR Disposition Design

Date: 2026-08-02  
Task: GOV-T02  
Status: accepted by the existing task charter and the user's standing instruction to continue with the recommended safe option

## Problem

PR #1 and PR #7 predate the `stable/kaiyuan-v2` release line. Neither targets
stable, both have diverged histories, and both remain open. Closing them without
proof could lose unique behavior; merging them would reintroduce obsolete
architecture and bypass the stable review chain.

## Approaches considered

### A. Evidence-first, two-stage closure — selected

Classify every changed path and every stated behavior against the exact current
stable head. Merge the audit evidence first. Only then add supersession comments
and close the legacy PRs. Record the actual closed state in a final docs-only
closeout.

This is reversible, auditable and keeps closure separate from code integration.

### B. Close first, document later — rejected

Closing is reversible, but the evidence could remain only in chat or be lost if
the documentation step fails.

### C. Leave both PRs open indefinitely — rejected

This avoids closure risk but preserves misleading merge surfaces and recurring
recovery cost even after stable replacement is proven.

## Evidence model

Each legacy changed path is classified as one of:

- `exact`: the stable blob SHA is identical;
- `evolved_superset`: stable retains the responsibility with later safety or
  feature work;
- `retired_non_behavioral`: obsolete task/plan scaffolding replaced by the
  current governance system;
- `unresolved`: no safe replacement proof; any such row blocks closure.

Semantic requirements from each PR body are checked independently of filename
identity. An ancestry comparison alone is insufficient because stable uses
reviewed/squashed integration.

## Closure protocol

1. Freeze current stable, PR base/head and changed-path identities.
2. Save the path/semantic matrix and zero-comment/review/thread evidence.
3. Require zero `unresolved` behavior or data rows.
4. Merge the docs-only audit PR into `stable/kaiyuan-v2`.
5. Comment on each legacy PR with the merged audit commit and replacement
   summary.
6. Close, never merge, each legacy PR.
7. Re-read GitHub state and publish a final docs-only closeout.

## Safety

No legacy commit is merged, rebased or cherry-picked. No corpus, candidate,
official ingest, Qdrant, `local_kb_default`, PR #54, B10-PR-D/E/F, B11/B12,
publishing or `main` state changes. Closure does not delete branches or data.
