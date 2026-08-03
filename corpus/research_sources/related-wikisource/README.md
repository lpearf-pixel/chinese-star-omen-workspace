# Related Wikisource research-source package

Status: B10 research support; not an official KB corpus and not a frozen multi-text schema.

## Purpose

This package preserves revision-bound Wikisource source objects used to audit Core14 passages and natural scholarly boundaries. It gives related works the same minimum provenance treatment as 《唐開元占經》 while keeping raw source, catalog metadata, case mapping and collation notes separate.

The B10-R05 bounded denominator is 7 work families, 31 fixed-revision source objects and 1,050,322 raw UTF-8 bytes. The original 20 Core14 research mappings remain unchanged; the 15 boundary-expansion objects carry no inferred Core14 case.

## Reversible layout

    corpus/research_sources/related-wikisource/
      README.md
      accession-working-contract.json
      b10-r05-bounded-expansion.json
      source-projection-pilot-v0.json
      p0/
        <work-family>/
          accessions.json
          raw/
            <accession-id>.<wikitext|txt>
          notes.md
      accession-manifest.json
      core14-mapping.json

One accession object identifies one Wikisource title at one fixed revision. A work can have several accessions when its treatise or volumes are separate pages. Files are additive: a later catalog or database can ingest them without rewriting the captured raw bytes.

## Source layers

- **raw snapshot**: exact UTF-8 content captured from the fixed source object; never replaced by normalized punctuation.
- **accession metadata**: source title, oldid, permanent URL, locator, revision/access time, version family, license note, hashes and limitations.
- **research mapping**: directional relationship to a Core14 case or atomic proposal.
- **notes**: suggested punctuation, translation and collation hypotheses; never silently merged into raw.

## Integrity and citation boundaries

- A floating current page is supplemental; the fixed oldid/permanent URL is the accession identity.
- SHA-256 and UTF-8 byte count bind the saved raw file.
- Wikisource and a same-family mirror are not independent witnesses solely because their transcriptions agree.
- `capture_status=complete` means the named page/revision was captured; it does not mean the ancient work is complete or critically edited.
- Whole-row citation and atomic citation remain separate decisions.
- Lost works or carrier-only quotations are stored as excerpts/identities, never fabricated full books.
- These files do not populate Reviewer A/B, freeze thresholds, approve rules, ingest the official KB, access Qdrant, or read/write `local_kb_default`.

## Attribution

Each accession records the source-page license/attribution statement and permanent source URL. Repository users must preserve the accession metadata and comply with the recorded source terms when redistributing snapshots.
