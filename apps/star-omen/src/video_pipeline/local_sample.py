from __future__ import annotations

from datetime import datetime

from src.video_pipeline.astronomy import SkyfieldEphemerisProvider
from src.video_pipeline.contracts import AstronomyEventV1, ObserverV1


def build_july_21_event(
    *,
    provider: SkyfieldEphemerisProvider,
    observer: ObserverV1,
    at_utc: datetime,
) -> AstronomyEventV1:
    return provider.calculate_angular_separation_event(
        primary_body="moon",
        target_modern_object_id="hip:65474",
        at_utc=at_utc,
        observer=observer,
    )


__all__ = ["build_july_21_event"]
