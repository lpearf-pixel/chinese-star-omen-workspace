# B9-PR-B Scientific Provider and Asterism Catalog Decision

## Status

```text
Task: B9-PR-B
Branch: codex/kaiyuan-b9-scientific-provider-v1
PR: #34
Base: stable/kaiyuan-v2 at 8bc8d0c8f91f78e4a4faceb22a037b9c526596c0
Evidence head before final docs: 08f1f860637003e07ec0cb906ff85a47833afee4
State: VERIFYING
```

## Accepted scientific boundary

1. Persisted public times are explicit UTC. Skyfield may internally use TT/TDB, but those scales are not silently serialized as UTC.
2. Identity coordinates use ICRS/J2000 source records; apparent coordinates use date-dependent apparent/GCRS semantics; ecliptic coordinates use ecliptic-of-date; topocentric altitude/azimuth uses WGS84 observer coordinates.
3. Scientific altitude is geometric and refraction-disabled. Any display refraction must be an explicit later rendering choice.
4. Longitude is east-positive; latitude is north-positive.
5. Runtime ephemeris download is forbidden. The provider only accepts a caller-supplied local `.bsp` file and expected SHA-256/size bounds.
6. The local file is validated before load, bound to device/inode/size/mtime/SHA-256, and rechecked after Skyfield opens it.
7. Toolchain provenance records logical names, versions, byte sizes and hashes, never machine absolute paths.

## Accepted asterism boundary

1. Chinese asterism mapping is exact catalog identity/membership/region data, never nearest-star inference.
2. Unknown objects return `unresolved`; ambiguous objects are narration-blocked.
3. `verified_identity` permits an explicit traditional star name only when source and confidence gates pass.
4. `verified_membership` permits membership-limited narration, not identity language.
5. `region_only` permits region-limited narration only.
6. Source snapshots are canonical JSON and SHA-256 bound. Upstream Git blob identity is recorded separately as `git-sha1`.

## Initial source-backed identity

```text
Modern object: HIP 65474 / Spica
Traditional star: 角宿一
Asterism: 角宿
Reference frame: ICRS J2000
RA: 201.298247375 deg
Dec: -11.161319472222223 deg
```

Sources:

- Stellarium Chinese sky-culture commit `3972e97101e4321079279b5e5660b074fafc030a`, upstream blob `fe8761576dc6c5cd4a65e3551a81ead6122c895f`, exact record `65474|_("角宿一") 1`;
- SIMBAD Spica identity snapshot retrieved `2026-07-22`, exact source record `HIP 65474 / Spica`.

Canonical snapshot SHA-256:

```text
Stellarium record: d036a7f37e3c27ca1197d93739d922808e2a0d60e57b96b7692e7d60ca711229
SIMBAD record: ecaa14864c3e94648d61a28929ef7e5d729b51d4c387ff2c57b40caf2d9d533d
```

## Verified local toolchain evidence

User-side isolated worktree collection on macOS 14.6.1 arm64:

```text
Python: 3.12.8
Skyfield: 1.51
skyfield-data: 7.0.0
jplephem: 2.24
dde421.bsp size: 16788480 bytes
de421.bsp SHA-256: a20a7139da04cbc462454634918e9a9ca69127044e2cc9d4f9c16e238d2deedc
```

The collector ran in a detached temporary worktree and did not alter the user's dirty `dev-test` checkout.

## TDD and review evidence

- initial RED: scientific/asterism modules absent;
- implementation review RED: strict enum parsing and alias canonicalization;
- review RED: `18 failed / 22 passed` exposed ephemeris TOCTOU, UTC output, source snapshot, fixture and status-boundary gaps;
- user-side evidence RED: `15 failed / 304 passed`, all cascading from one stale SIMBAD snapshot hash;
- focused exact-head gate after correction: `40 passed in 1.66s`;
- full downstream exact-head regression: `319 passed in 3.75s`;
- Development Governance `30476222345` — success;
- Kaiyuan Stable Core `30476222775` — success;
- Kaiyuan Upstream Runtime `30476222618` — success;
- B9 Scientific Provider `30476222362` — success;
- review threads: 0;
- submitted reviews: 0.

## Explicit exclusions

No KB retrieval, RuleAssessment adapter, classical evidence, omen judgment, editorial compiler, Stellarium execution, FFmpeg/media, publishing, corpus/candidate/ingest/Qdrant mutation or `local_kb_default` access is part of B9-PR-B.

## Follow-on boundary

B9-PR-C may consume the frozen `AstronomyEvent/v1` and source-backed asterism resolution, but must not mutate B9-PR-B scientific facts or silently upgrade unresolved/ambiguous mappings. Breaking scientific or catalog semantics require a new version or an explicit compatibility decision.
