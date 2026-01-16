from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..models import Alignment, NormalizedEvent


@dataclass
class AlignConfig:
    # Acceptable max delta when searching for an anchor.
    anchor_window_ms: int = 5 * 60_000


def estimate_offset_from_session_start(
    *,
    app_open_video_ms: int,
    events: Iterable[NormalizedEvent],
    cfg: AlignConfig = AlignConfig(),
) -> Alignment:
    """Estimate alignment offset using a session_start anchor.

    offset_ms is computed as:
      offset = session_start_event_ms - app_open_video_ms

    This is intentionally simple for MVP. Improve later with multiple anchors and drift.
    """

    starts = [e for e in events if e.kind == "session_start"]
    if not starts:
        return Alignment(offset_ms=0, drift_ppm=0.0, anchors=[], score=0.0)

    # Choose the earliest session_start as default anchor.
    anchor = min(starts, key=lambda e: e.t_event_ms)
    offset = int(anchor.t_event_ms - app_open_video_ms)

    # Score is higher if session_start appears soon after app open.
    delta = abs(anchor.t_event_ms - (app_open_video_ms + offset))
    score = max(0.0, 1.0 - (delta / max(1, cfg.anchor_window_ms)))

    return Alignment(
        offset_ms=offset,
        drift_ppm=0.0,
        anchors=[{"kind": "session_start", "t_video_ms": app_open_video_ms, "t_event_ms": anchor.t_event_ms}],
        score=score,
    )
