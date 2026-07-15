# kb-text-core

Shared, read-only text parsing and matching primitives for the Kaiyuan corpus.

The package keeps raw text immutable, normalizes only the search view, preserves
original character offsets, extracts page/heading anchors, ranks `fenjuan`
before duplicate `fulltext` hits, and is shared by fallback retrieval and
candidate generation.
