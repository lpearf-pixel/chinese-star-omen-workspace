# B9-PR-B Scientific Provider and Asterism Catalog Closeout

## 2026-07-30 — implementation merged

```text
Repository: lpearf-pixel/chinese-star-omen-workspace
Release branch: stable/kaiyuan-v2
Feature branch: codex/kaiyuan-b9-scientific-provider-v1
PR: #34
Base before merge: 8bc8d0c8f91f78e4a4faceb22a037b9c526596c0
Final feature head: 3493270f65f2d177a9c755078477512fa585c0bb
Development Governance: 30476661474 — success
B9 Scientific Provider: 30476655763 — success
Kaiyuan Stable Core: 30476656261 — success
Kaiyuan Upstream Runtime: 30476655660 — success
Squash merge: c72aa7630f58c5828b8343bcdd39c369efe1df76
```

## Delivered

- versioned UTC/TT/TDB, coordinate-frame, observer and refraction conventions;
- verified local `.bsp` boundary with size/SHA-256/device/inode/mtime checks and pre/post-load revalidation;
- offline Skyfield 1.51 provider using pinned `skyfield-data==7.0.0`;
- deterministic body/fixed-star coordinates, moon phase, phase transitions, topocentric alt/az and angular separation;
- path-free toolchain provenance;
- source-bound Chinese asterism catalog with exact ID/alias lookup and no nearest-star fallback;
- canonical Stellarium/SIMBAD source snapshots and astronomy/asterism fixtures;
- source-backed `HIP 65474 / Spica = 角宿一` identity;
- deterministic narration boundaries for verified identity, verified membership, region only, ambiguous and unresolved states;
- dedicated scientific provider CI with retained focused-test logs.

## Evidence

```text
Focused exact-head: 40 passed in 1.66s
Full downstream exact-head: 319 passed in 3.75s
Review threads: 0
Submitted reviews: 0
Changed files: 28 expected scientific/catalog/test/governance files
```

User-side isolated worktree validation:

```text
macOS: 14.6.1 arm64
Python: 3.12.8
Skyfield: 1.51
skyfield-data: 7.0.0
de421.bsp size: 16788480 bytes
de421.bsp SHA-256: a20a7139da04cbc462454634918e9a9ca69127044e2cc9d4f9c16e238d2deedc
```

Source identities:

```text
Stellarium snapshot SHA-256: d036a7f37e3c27ca1197d93739d922808e2a0d60e57b96b7692e7d60ca711229
Stellarium upstream Git blob SHA-1: fe8761576dc6c5cd4a65e3551a81ead6122c895f
SIMBAD snapshot SHA-256: ecaa14864c3e94648d61a28929ef7e5d729b51d4c387ff2c57b40caf2d9d533d
```

## TDD and review history

- missing-module RED;
- strict enum and alias canonicalization RED;
- independent scientific-boundary RED: `18 failed / 22 passed`;
- user-side stale-source-hash RED: `15 failed / 304 passed`;
- one remaining stale test-field RED: `1 failed / 39 passed`;
- corrected exact-head focused and full regressions green.

## Safety boundary

No KB retrieval, RuleAssessment adapter, classical evidence, omen judgment, editorial compiler, Stellarium execution, FFmpeg/media, publishing, corpus/candidate/ingest/Qdrant mutation or `local_kb_default` access occurred in B9-PR-B.

## Follow-on

B9-PR-C must start from the closeout merge's new stable HEAD and may consume only frozen `AstronomyEvent/v1` plus source-backed asterism resolutions. It must not mutate B9-PR-B scientific semantics or silently upgrade unresolved/ambiguous mappings.
