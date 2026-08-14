# Kaiyuan Twenty-eight Mansions and External-media Audit Design

**Status:** APPROVED
**Approved by user:** 2026-08-12
**Task:** ASTRO-R01
**Branch:** `codex/kaiyuan-28-mansions-external-audit-v1`
**Base:** `stable/kaiyuan-v2@c2e8fcabb04354fd14d0c72b3b6020a47e63a583`

## 1. Goal

Build one source-bound scientific foundation that can answer three different
questions without collapsing their meanings:

1. Which modern catalogue stars are members of a traditional asterism?
2. Is an observed body inside a Chinese lunar-mansion region?
3. What exactly did an external video claim, and how well does that claim map
   to astronomical measurement, classical text and modern inference?

毕宿 is the first complete gold sample. The same contracts then expand to all
twenty-eight mansions and feed the existing navigation cards. External media is
always a research lead, never a rule authority.

## 2. Accepted source model

### 2.1 Traditional identity and membership

Stellarium Chinese sky culture commit
`3972e97101e4321079279b5e5660b074fafc030a` is a pinned mapping source, not the
sole scientific authority. Its fixed records identify the eight base members:

| Traditional star | HIP |
|---|---:|
| 毕宿一 | 20889 |
| 毕宿二 | 20648 |
| 毕宿三 | 20455 |
| 毕宿四 | 20205 |
| 毕宿五 | 21421 |
| 毕宿六 | 20885 |
| 毕宿七 | 20713 |
| 毕宿八 | 18724 |

The same commit's `index.json` line graph contains those eight stars plus HIP
21683, which is 附耳. 附耳 is related to the line drawing but is not a ninth
毕宿 member. The data contract therefore keeps `member_object_ids` and
`related_object_ids` separate.

Coordinates and proper motions are bound to CDS VizieR catalogue I/239,
Hipparcos Main Catalogue (ESA 1997). Display geometry is never used to invent
coordinates. Hipparcos positions retain their J1991.25 catalogue epoch and are
propagated with both proper-motion components before apparent-of-date
calculation.

### 2.2 Mansion region

The pinned Chinese sky-culture `lunar_system.defining_stars` list defines the
western edge of each mansion. The next defining star is the eastern edge. The
edges are equatorial great circles running from celestial pole to celestial
pole, as documented by the pinned Stellarium sky-culture guide.

For 毕宿:

```text
western defining star: HIP 20889 / 毕宿一
eastern defining star: HIP 26207 / 觜宿一
coordinate system: apparent equatorial of date
interval convention: west inclusive, east exclusive
```

This is a versioned modern computational representation of the traditional
lunar-mansion system. It must be labelled `derived_region`; it is not described
as a surviving ancient polygon or an original historical boundary survey.

### 2.3 Relation semantics

The system reports objective measurements separately from classical relation
terms:

| Output | Minimum evidence |
|---|---|
| `in_mansion_region` | target and both defining stars in one explicit equatorial frame and epoch |
| `nearest_member` | target and all verified member positions in one explicit frame and epoch |
| `near_asterism` | nearest-member separation plus an explicit versioned threshold |
| `入` | at least two time samples proving an outside-to-inside transition |
| `犯` | versioned distance/contact rule plus the relevant target geometry |
| `守` | versioned distance rule plus continuous duration evidence |
| `留` | versioned apparent-speed/stationary rule plus duration evidence |

An unqualified `临毕` never maps automatically to one of these terms. A
single-time assessment returns `ambiguous_relation` together with the objective
region and nearest-member measurements.

## 3. Catalog architecture

`asterism-catalog/v1` receives additive optional sections; the existing Spica
entry and public behavior remain compatible.

```text
entries[]
  exact star identities and memberships

asterisms[]
  asterism ID, aliases, ordered base members, related stars, defining star,
  line segments, source refs and completeness state

lunar_mansions[]
  sequence, western/eastern defining stars, boundary model, source refs and
  completeness state
```

All referenced object and source IDs must exist. Member lists, related lists,
line segments and mansion sequence numbers are unique. A complete asterism may
not contain ambiguous or unresolved member mappings. A complete twenty-eight
mansion catalog must contain exactly sequence 1 through 28 and form a closed
boundary cycle.

## 4. Computation architecture

`mansion_regions.py` is a pure, offline module. It accepts same-frame positions,
normalizes circular right ascension, handles the 0/360-degree wrap and calculates
spherical angular separation. It does not fetch ephemerides or source data.

`SkyfieldEphemerisProvider` is the adapter that obtains apparent positions of
the target body and defining/member stars at one UTC instant. It passes those
positions to the pure evaluator and records toolchain/catalog hashes through the
existing scientific provenance boundary.

No result is upgraded to a classical rule or weather prediction.

## 5. Navigation architecture

The existing twenty-eight-mansion overview and mansion cards are derived
research navigation, not raw classical corpus. Each card gains a bounded
scientific-status block:

```text
catalog status
traditional members
defining star
mansion boundaries
modern catalogue IDs
source revision IDs
known unresolved/ambiguous mappings
```

Simplified display aliases and traditional filenames must resolve to the same
card. Link validation prevents silent `毕宿`/`畢宿`, `娄宿`/`婁宿`, `参宿`/`參宿`,
`张宿`/`張宿` and `轸宿`/`軫宿` breakage.

## 6. External-media evidence architecture

After the scientific gold sample is stable, external content uses four strict
research-only contracts:

- `ExternalMediaSource/v1`: platform, creator, work ID, fixed URL, publication
  time, captured text/image hashes and rights/capture notes.
- `ExternalClaim/v1`: atomic claim class (`astronomy_fact`, `classical_quote`,
  `historical_correspondence`, `modern_inference`, `disclaimer`) and exact source
  span.
- `EvidenceLink/v1`: source-bound classical passage, astronomy calculation,
  historical record or modern authority.
- `ExternalAudit/v1`: `supported_exact`, `partial`, `source_missing`,
  `ambiguous`, `contradicted` or `modern_inference_only`.

The first inventory is 祖山觀's 23-item collection; nine priority works are
audited, with the “毕宿天象的烈风，能不能对应海上风暴？” work as the complete
gold sample. Other creators enter through bounded 5–10 work samples.

## 7. Safety and governance

- No external video becomes classical evidence or an approved rule.
- “烈风” is not silently equated with typhoon, tropical cyclone or maritime
  storm.
- Models may transcribe and propose claim splits but may not approve them.
- Unknown and ambiguous star mappings remain explicit.
- No raw corpus rewrite, Reviewer A/B substitution, threshold freeze, official
  ingest, Qdrant or `local_kb_default` access.
- No work on `main`; release target remains `stable/kaiyuan-v2` through a PR.
- PR #54 and #64 remain independent Drafts and are not modified by ASTRO-R01.

## 8. Delivery phases

1. 毕宿 gold sample and generic catalog/region evaluator.
2. All 28 defining stars and closed mansion-region cycle.
3. All mansion member/line identities with explicit completeness states.
4. Navigation status blocks and link validation for all 28 cards.
5. External-media contracts, 祖山觀 inventory and nine priority audits.
6. Bounded expansion to other creators.

Each phase must be independently testable and reviewable. Later phases may
consume earlier frozen interfaces but must not rewrite their source identities.
