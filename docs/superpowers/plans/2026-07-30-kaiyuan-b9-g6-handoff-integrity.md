# B9-G6 Handoff Integrity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bind B9-G6 capability evidence to the actual Stellarium application
version and create a privacy-safe, fixed-member, deterministic handoff archive.

**Architecture:** A dependency-free Python CLI reads
`CFBundleShortVersionString` from the supplied `.app`, validates it against the
existing capability JSON, derives a relative screenshot inventory from exact
PNG bytes, and writes an exclusively published tar.gz from an explicit member
list. The existing renderer, review, package, and capability contracts remain
unchanged.

**Tech Stack:** Python 3.12 standard library (`argparse`, `gzip`, `hashlib`,
`json`, `os`, `plistlib`, `tarfile`, `tempfile`), pytest.

## Global Constraints

- Target only `stable/kaiyuan-v2`; never `main`.
- Do not access or mutate corpus, candidates, ingest, retrieval, Qdrant, or
  `local_kb_default`.
- Do not change scientific content, preview bytes, screenshots, assisted-review
  decisions, or publication authority.
- Accept Stellarium `major.minor` or `major.minor.patch`, normalize to three
  components, and require supported series `26.x`.
- Archive only the fixed evidence member set and regular non-symlink PNGs.
- Generate relative screenshot inventory entries in memory.
- Never overwrite an existing archive.
- Keep rejected historical runs immutable.

---

### Task 1: Register the remediation and reproduce the handoff failures

**Files:**

- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/PROJECT_MEMORY.md`
- Modify: `docs/development/WORK_LOG.md`
- Create: `tests/test_b9_g6_handoff_script.py`

**Interfaces:**

- Consumes: the accepted design at
  `docs/superpowers/specs/2026-07-30-kaiyuan-b9-g6-handoff-integrity-design.md`.
- Produces: task `B9-G6-E6` in state `IN_PROGRESS` and executable behavior
  regressions for `scripts/b9_g6_handoff.py`.

- [x] **Step 1: Register B9-G6-E6 before behavior implementation**

Record the uploaded archive SHA-256
`0271e15b99151811123ff47f25e5254dec42703001e6bc8079344e6f66916918`,
the valid core review chain, and the three rejecting defects: claimed
Stellarium `26.2.0` versus visible `26.1`, five absolute inventory paths, and
sixteen AppleDouble members.

- [x] **Step 2: Write a real synthetic app/evidence fixture**

Create complete temporary evidence bytes for every required file, an
`Info.plist` containing `CFBundleShortVersionString`, regular PNGs, unrelated
files, and `._*` files. Expected archive member names and inventory hashes must
be hand-derived literals from fixture bytes.

- [x] **Step 3: Write the version-mismatch RED**

```python
completed = run_handoff(
    stellarium_version="26.1",
    capability_version="26.2.0",
)
assert completed.returncode == 1
assert "does not match the installed Stellarium version 26.1.0" in completed.stderr
assert not completed.output.exists()
```

- [x] **Step 4: Write the clean-archive RED**

```python
completed = run_handoff(
    stellarium_version="26.1",
    capability_version="26.1.0",
)
assert completed.returncode == 0
assert archive_names(completed.output) == EXPECTED_MEMBER_NAMES
assert read_inventory(completed.output) == [
    f"{SCREEN_1_SHA256}  screenshots/01-stellarium-overview.png",
    f"{SCREEN_2_SHA256}  screenshots/subtitle-01.png",
]
```

Also assert no member begins with `._`, no inventory path is absolute, symlink
inputs fail, existing output remains unchanged, and repeated clean inputs yield
identical archive bytes.

- [x] **Step 5: Run RED**

Run:

```bash
python -m pytest tests/test_b9_g6_handoff_script.py -q
```

Expected: collection or execution fails because
`scripts/b9_g6_handoff.py` does not exist.

- [x] **Step 6: Commit the verified RED and task registration**

```bash
git add \
  docs/development/TASKS.md \
  docs/development/PROJECT_MEMORY.md \
  docs/development/WORK_LOG.md \
  tests/test_b9_g6_handoff_script.py
git commit -m "test: reproduce B9 G6 handoff integrity failures"
```

### Task 2: Implement the fail-closed handoff packager

**Files:**

- Create: `scripts/b9_g6_handoff.py`
- Test: `tests/test_b9_g6_handoff_script.py`

**Interfaces:**

- Produces:
  `normalize_stellarium_version(value: str) -> str`,
  `read_stellarium_version(app: Path) -> str`,
  `build_screenshot_inventory(evidence_dir: Path) -> tuple[bytes, list[Path]]`,
  `create_handoff_archive(evidence_dir: Path, stellarium_app: Path, output: Path) -> Path`,
  version-only CLI mode, and `main(argv: list[str] | None = None) -> int`.

- [x] **Step 1: Implement version parsing and binding**

Use `plistlib.load()` on `Contents/Info.plist`. Require a string matching
`^[0-9]+\.[0-9]+(?:\.[0-9]+)?$`, append `.0` when needed, require major `26`,
then load `local-capability-evidence.json` with duplicate-key and non-finite
value rejection. Require its `schema_version` and `stellarium_version` to match
the actual normalized version. Expose `--print-stellarium-version` so the same
normalized value is used when capability evidence is rebuilt.

- [x] **Step 2: Implement fixed evidence enumeration**

Require the twelve source root files listed in the design, excluding the
caller-provided `screenshot-sha256.txt`. Enumerate sorted `screenshots/*.png`,
reject names beginning with `._`, symlinks, non-files, zero screenshots, and
more than 30 screenshots. Derive inventory lines as:

```python
f"{sha256}  screenshots/{path.name}\n"
```

- [x] **Step 3: Implement deterministic tar.gz bytes**

Use `gzip.GzipFile(filename="", mtime=0)` and `tarfile.open(mode="w",
format=tarfile.PAX_FORMAT)`. For every member set `uid=gid=0`, empty
`uname/gname`, `mtime=0`, and fixed regular-file/directory modes. Add only
explicit source bytes plus the in-memory inventory.

- [x] **Step 4: Implement no-overwrite publication**

Create a same-directory temporary file, fsync it, then publish with
`os.link(temp, output)`. Convert `FileExistsError` into an actionable CLI
failure and always remove only the temporary file.

- [x] **Step 5: Run focused GREEN**

Run:

```bash
python -m pytest tests/test_b9_g6_handoff_script.py -q
```

Expected: all tests pass with zero warnings.

- [x] **Step 6: Commit the implementation**

```bash
git add scripts/b9_g6_handoff.py tests/test_b9_g6_handoff_script.py
git commit -m "feat: secure B9 G6 evidence handoff"
```

### Task 3: Integrate the command, verify, and publish a Draft PR

**Files:**

- Modify: `docs/development/B9_VERTICAL_SLICE_RUNBOOK.md`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/PROJECT_MEMORY.md`
- Modify: `docs/development/WORK_LOG.md`

**Interfaces:**

- Consumes: `scripts/b9_g6_handoff.py`.
- Produces: one canonical operator command and exact-head verification evidence.

- [x] **Step 1: Replace the manual handoff steps**

The runbook must obtain and validate the actual application version through the
new CLI and replace `find | shasum` plus platform `tar` with:

```bash
python ../../scripts/b9_g6_handoff.py \
  --evidence-dir "$B9_EVIDENCE_DIR" \
  --stellarium-app "/Applications/Stellarium.app" \
  --output "data/b9-local-g6-evidence-${B9_RUN_ID}.tar.gz"
```

Explain that an existing mismatched capability JSON must be rebuilt using the
normalized version reported from the same app bundle before packaging.

- [x] **Step 2: Move B9-G6-E6 to VERIFYING**

Record focused results and keep B9 overall `VERIFYING`, run
`20260730T121805Z` unaccepted, and B10 `BLOCKED` until a regenerated archive
passes independent verification and final B9 closeout merges.

- [ ] **Step 3: Run relevant verification**

Run:

```bash
python -m pytest tests/test_b9_g6_handoff_script.py -q
python -m pytest \
  tests/test_collect_b9_g6_macos_evidence_script.py \
  tests/test_b9_preview_script.py -q
python -m compileall -q scripts apps/star-omen/src
bash -n scripts/collect_b9_g6_macos_evidence.sh
git diff --check
```

Then run the repository contract, text-core, downstream, and governance gates
required by `DEVELOPMENT_MANUAL.md`.

- [x] **Step 4: Independently pressure-test the uploaded failure**

Run the new command against a fixture reflecting the uploaded mismatch and
verify it refuses publication. Run it against corrected version metadata and
verify tar member safety, relative inventory, byte hashes, and absence of
`._*`.

- [ ] **Step 5: Commit exact verification evidence**

```bash
git add \
  docs/development/B9_VERTICAL_SLICE_RUNBOOK.md \
  docs/development/TASKS.md \
  docs/development/PROJECT_MEMORY.md \
  docs/development/WORK_LOG.md
git commit -m "docs: verify B9 G6 handoff integrity"
```

- [ ] **Step 6: Publish only to the stable release line**

Push `codex/kaiyuan-b9-g6-handoff-integrity-v1`, create a Draft PR targeting
only `stable/kaiyuan-v2`, audit changed files, and require exact-head workflows
before merge. Do not retarget `main`.
