# GOV-T04 Major-Version Unified Runner Runbook

## Purpose

`Kaiyuan Major-Version Unified Gate` is the only migrated remote Runner entry
for a major-version candidate preparing to merge into
`stable/kaiyuan-v2`. Routine pull requests and branch pushes do not start these
workflows. Only a lightweight tag named `kaiyuan-runner/v2/<exact-sha>` starts
the unified gate. Focused and applicable regression checks remain local-first.

This run does not replace nightly quality work, real macOS/Stellarium/FFmpeg
evidence, corpus/scientific review, human Reviewer A/B, migrations, security or
production release evidence.

## Entry conditions

Before creating the candidate tag:

1. all intended code, tests and documentation are committed on one candidate
   branch in `lpearf-pixel/chinese-star-omen-workspace`;
2. the branch contains the current `stable/kaiyuan-v2` HEAD and is strictly
   ahead of it;
3. focused and applicable local gates passed and their commands/results are in
   `WORK_LOG.md`;
4. review has no unresolved Critical or Important finding;
5. the full candidate commit SHA is copied with `git rev-parse HEAD`.

Do not create a tag from a short SHA, stale branch, uncommitted work or another
repository. Do not use an annotated tag; the gate accepts only a lightweight
tag whose ref directly identifies a commit.

## Trigger with an exact-SHA tag

From the clean candidate branch:

```bash
candidate_sha=$(git rev-parse HEAD)
test "$(printf '%s' "$candidate_sha" | wc -c | tr -d ' ')" = 40
git merge-base --is-ancestor origin/stable/kaiyuan-v2 "$candidate_sha"

runner_tag="kaiyuan-runner/v2/$candidate_sha"
if git show-ref --verify --quiet "refs/tags/$runner_tag"; then
  echo "candidate tag already exists: $runner_tag" >&2
  exit 1
fi

git tag "$runner_tag" "$candidate_sha"
test "$(git cat-file -t "$runner_tag")" = commit
git push origin "refs/tags/$runner_tag"
```

`git tag <name> <sha>` without `-a`, `-s` or `-m` creates the required
lightweight tag. Record the resulting workflow run ID and attempt. Preserve the
tag as audit evidence; do not move or force-push it.

The preflight rejects the run unless all of these are true:

```text
candidate_sha is lowercase 40-hex
ref type is tag
tag name == kaiyuan-runner/v2/<candidate_sha>
tag object type is commit
candidate_sha == tag-push event SHA
candidate_sha == checked-out HEAD
candidate_sha != current stable HEAD
current stable HEAD is the exact merge base of the candidate
```

If preflight rejects a stale candidate, update the branch from stable, rerun
local gates, commit any governance state change, and create a new exact-SHA tag.

## Required job set

The unified run is complete only when preflight and all eight reusable groups
succeed:

```text
preflight
Development Governance
B9 Assisted Renderer Review
B9 Editorial Stellarium
B9 Package Review Preview
B9 RuleAssessment Lineage
B9 Scientific Provider
Kaiyuan Stable Core
Kaiyuan Upstream Runtime
```

The finalizer runs even when a dependency fails. `skipped`, `cancelled`,
`failure`, missing output or artifact upload failure is a failed unified gate,
not a partial pass.

## Evidence verification

Download the artifact named:

```text
major-version-runner-result-<run_id>-<run_attempt>
```

It must contain exactly:

```text
major-version-runner-result.json
major-version-runner-result.json.sha256
```

Verify locally from the extracted artifact directory:

```bash
sha256sum -c major-version-runner-result.json.sha256

python3 - <<'PY'
import json
from pathlib import Path

result = json.loads(Path("major-version-runner-result.json").read_text())
assert result["schema_version"] == "major-version-runner-result/v1"
assert result["candidate_sha"] == result["event_sha"]
assert result["candidate_sha"] == result["verified_candidate_sha"]
assert result["trigger_ref"] == f'refs/tags/kaiyuan-runner/v2/{result["candidate_sha"]}'
assert result["trigger_ref_type"] == "tag"
assert len(result["candidate_sha"]) == 40
assert len(result["base_sha"]) == 40
assert len(result["job_results"]) == 9
assert set(result["job_results"].values()) == {"success"}
assert result["all_required_succeeded"] is True
print(result["run_id"], result["run_attempt"], result["candidate_sha"])
PY
```

Match printed run ID, attempt, candidate SHA and base SHA to the GitHub run and
the recorded release candidate. Save the JSON SHA-256 in `WORK_LOG.md`.

Immediately before marking the PR ready or merging, fetch the live stable ref
and require it to equal the artifact's `base_sha`:

```bash
git fetch --no-tags origin \
  +refs/heads/stable/kaiyuan-v2:refs/remotes/origin/stable/kaiyuan-v2
live_base_sha=$(git rev-parse refs/remotes/origin/stable/kaiyuan-v2)
artifact_base_sha=$(python3 -c \
  'import json; print(json.load(open("major-version-runner-result.json"))["base_sha"])')
test "$live_base_sha" = "$artifact_base_sha"
```

If stable moved, update the candidate from the new stable HEAD, rerun all
applicable local gates and review, and create a new lightweight exact-SHA tag.
Do not merge a green candidate onto an unverified newer base.

## Invalidation and retry

Any candidate commit after a successful run invalidates it, including a
status-only or documentation commit. Any movement of `stable/kaiyuan-v2` also
invalidates the artifact because its recorded `base_sha` is no longer the live
merge base. Run applicable local gates again and create one new exact-SHA tag.
Do not move/force-push an old tag, reuse a green run from an ancestor or rerun
the same failed head merely to hide a deterministic failure.

Runner unavailable or incomplete is recorded as `BLOCKED` or `NOT RUN`. It may
not be recorded as passed, and the major-version candidate may not merge into
stable. Unrelated routine development may continue locally.

## Merge and rollback

After the exact final head has a verified successful unified artifact and clean
review, merge only to `stable/kaiyuan-v2` with an expected-head lock. Recheck
the stable merge SHA and branch identity after merge. Never retarget to `main`.

Workflow rollback is a revert of the GOV-T04 merge. It does not require schema,
corpus, Qdrant, collection or production data rollback. Re-enabling automatic
PR/branch-push triggers or adding a default-branch manual launcher requires a
new explicit governance decision; it is not part of the rollback procedure.
