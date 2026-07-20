# Kaiyuan Evidence-Backed Astronomical Short Video Pipeline Design

## Scope

B9 adds a review-first pipeline that turns a date, observation location, and candidate celestial event into a traceable short-video production package. The package combines verified modern astronomy, Chinese asterism mapping, citable 《唐開元占經》 evidence, an explicitly labelled modern interpretation, a Stellarium scene script, subtitles, and a render manifest.

The first milestone does not auto-publish to Douyin and does not allow a language model or template to convert uncertain evidence into a classical claim. It produces a reviewable artifact bundle and an optional local MP4 preview. The downstream `apps/star-omen` application remains read-only with respect to official Qdrant data.

## Approaches considered

1. **Evidence package first, local rendering second (selected).** Build a deterministic, versioned package before starting Stellarium or FFmpeg. This keeps astronomy, classical evidence, editorial interpretation, and rendering independently testable and lets the same package be reviewed or re-rendered later.
2. **Direct prompt-to-video generation.** This is fast but cannot reliably separate astronomy facts, classical quotations, and modern copy; it also makes evidence drift and correction difficult to audit.
3. **Stellarium-only show script.** This produces attractive sky footage but does not solve source retrieval, historical interpretation, subtitles, review state, or publication provenance.

## User-facing output

One run creates a directory containing:

```text
video-package.json
astronomy.json
evidence.json
editorial.json
script.md
shot-list.json
stellarium/show.ssc
subtitles/zh-CN.srt
render/render-manifest.json
review.json
```

Optional local rendering adds:

```text
render/frames/*.png
render/preview.mp4
render/final.mp4
```

Every file is generated from the versioned `video-package/v1` contract. The package records source hashes, corpus version, collection, calculation inputs, exact UTC timestamps, observer coordinates, rule-match status, evidence status, and the tool versions used to generate assets.

## Claim classes and editorial boundary

Every sentence or shot annotation belongs to exactly one claim class:

- `astronomy_fact`: calculated time, coordinates, angular separation, visibility, phase, rise/set, or object identity.
- `classical_quote`: exact citable primary evidence that passes source, locator, page, paragraph, heading, anchor, and hash validation.
- `historical_context`: a sourced explanation of the historical star-omen system that is not presented as a verbatim quotation.
- `modern_interpretation`: contemporary creative wording such as “开口破局”; it must never be labelled as an ancient rule or quotation.
- `production_instruction`: camera, subtitle, transition, music, or timing instructions with no factual claim.

The editorial compiler rejects unclassified narration segments, classical quotations without citable evidence, and modern interpretations that claim inevitability or impersonate a primary source.

## Architecture and data flow

### 1. Astronomy candidate generation

A concrete Skyfield-backed provider implements the existing `EphemerisProvider` boundary. It calculates deterministic positions for configured bodies and timestamps. A detector produces normalized event candidates with UTC time, observer location, angular separation, altitude, visibility status, and calculation provenance.

Missing or non-finite astronomy inputs fail closed. An event with incomplete required measurements remains `insufficient_data` and cannot proceed to a publishable package.

### 2. Chinese asterism mapping

The asterism matcher maps calculated positions to the project’s asterism catalog. Modern object identifiers and Chinese star names are both retained. Confidence, matching method, catalog version, and unresolved aliases are recorded. A low-confidence or unresolved mapping may produce a research candidate but not a publishable classical claim.

### 3. Classical evidence and rule execution

The pipeline reuses the official two-stage retrieval order:

```text
official Qdrant structured recall
→ official Qdrant primary evidence
→ read-only filesystem primary fallback only when official primary is empty
```

Retrieved passages pass through the existing citable evidence resolver. The event then runs through the existing rule engine, including three-valued conditions, conflict resolution, evidence status, and candidate-only handling. Pending candidate overlays may appear as research leads but never as final classical evidence.

### 4. Editorial package compiler

A deterministic compiler turns the event, evidence, and rule result into a structured editorial outline. Templates provide the selected 60–90 second rhythm:

```text
0–5s      date/event hook
5–18s     verified sky phenomenon
18–32s    Chinese asterism identification
32–48s    classical source and historical context
48–67s    modern cultural interpretation
67–78s    bounded action suggestion and source disclosure
```

The first implementation generates copy from constrained templates and supplied editorial fields. Free-form model-assisted rewriting, when later added, must consume and return the same claim-labelled structure and pass the same validator.

### 5. Stellarium scene generation

The renderer adapter converts `shot-list.json` into a deterministic `.ssc` script. It sets date, location, projection, field of view, sky culture, labels, atmosphere, selected objects, camera moves, pauses, and screenshots. The local runner supports either Stellarium’s `--startup-script` command-line option or the Remote Control script endpoint. It writes only inside the caller-selected package directory.

Stellarium is a visualization renderer, not the authoritative astronomy calculator. The package preserves the Skyfield calculation separately and checks that Stellarium scene targets refer to the same body, time, and location.

### 6. Subtitle, audio, and MP4 assembly

The subtitle compiler derives exact time spans from the shot list and narration segments. FFmpeg assembles screenshot sequences or captured clips into a vertical `1080x1920` preview. A provided narration audio file may be aligned to the subtitle timeline; without audio, the pipeline creates a subtitle-only preview and leaves `final.mp4` blocked.

The first release does not silently call an external voice service. A future `NarrationRenderer` adapter may be added without changing the evidence package contract.

### 7. Human review and publish gate

`review.json` stores independent decisions for astronomy, classical evidence, editorial wording, and visual rendering. The publish gate requires:

- astronomy status `verified`;
- asterism mapping `verified` or explicitly absent from classical claims;
- every `classical_quote` backed by citable primary evidence;
- unresolved or candidate-only evidence excluded from final narration;
- all modern interpretations visibly classified;
- render manifest hashes matching actual assets;
- a human reviewer approval and timestamp.

The pipeline does not upload or publish to Douyin.

## First reference package

The first end-to-end fixture is the shared “2026-07-21 special celestial event” topic. It is intentionally stored as a candidate until the exact event, location-specific visibility, Chinese asterism mapping, and 《唐開元占經》 evidence are recalculated and reviewed. The phrase “开口破局” is classified only as `modern_interpretation`, never as a classical quotation.

## Safety and repository boundaries

- Target only `stable/kaiyuan-v2` through a feature branch and pull request.
- Never delete, recreate, migrate, or write `local_kb_default`.
- `apps/star-omen` does not perform official ingest or Qdrant mutation.
- Raw corpus bytes, page markers, original glyphs, and `&KRxxxx;` entities remain immutable.
- A missing transport response, unavailable runtime, ambiguous mapping, incomplete astronomy measurement, or failed citation validation is not converted into a healthy empty result.
- Generated media, screenshots, narration audio, and MP4 files are local artifacts and are not committed to Git.
- The source video analysis remains `partial_metadata_only` until an actual transcript or frame-level review is available.

## Test strategy

TDD covers contract validation, deterministic astronomy fixtures, non-finite and missing data, asterism confidence, official-primary-before-fallback ordering, citation enforcement, claim classification, modern-interpretation disclosure, deterministic Stellarium script generation, path confinement, subtitle timing, render manifest hashing, review-state transitions, and a hermetic end-to-end package that does not start Stellarium, FFmpeg, network services, Qdrant mutation, or publishing.