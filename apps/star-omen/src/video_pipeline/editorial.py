"""Stable public surface for B9 editorial compilation."""

from .editorial_impl import (
    ClassicalQuoteAssetV1,
    EditorialPackageV1,
    EditorialShotV1,
    EditorialTemplateSnapshotV1,
    EditorialTemplateV1,
    HistoricalContextAssetV1,
    ModernInterpretationAssetV1,
    canonical_editorial_bytes,
    compile_editorial_package,
    load_editorial_template,
)

__all__ = [
    "ClassicalQuoteAssetV1",
    "EditorialPackageV1",
    "EditorialShotV1",
    "EditorialTemplateSnapshotV1",
    "EditorialTemplateV1",
    "HistoricalContextAssetV1",
    "ModernInterpretationAssetV1",
    "canonical_editorial_bytes",
    "compile_editorial_package",
    "load_editorial_template",
]
