from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from ..models import Alignment, NormalizedEvent, Observation, UXState


@dataclass
class ResolutionResult:
    session_key: Optional[str]
    device_key: Optional[str]
    rationale: Dict[str, object]
    candidates: List[Dict[str, object]]


def find_app_open_time_ms(observations: List[Observation]) -> Optional[int]:
    for obs in observations:
        if obs.state == UXState.APP_OPEN:
            return obs.t_video_ms
    return None


def infer_session_from_events(
    *,
    events: Iterable[NormalizedEvent],
    app_open_video_ms: int,
    alignment: Alignment,
    top_k: int = 3,
) -> ResolutionResult:
    """Infer the most likely session (visit) from events within a time window.

    Generic heuristic:
    - group by event.session_key
    - score highest if there is a kind == 'session_start' nearest to app_open

    Note: this assumes the adapter maps the "first event" of a session to kind='session_start'.
    """

    # Convert app_open to estimated event-time using alignment.
    app_open_event_ms = app_open_video_ms + alignment.offset_ms

    by_session: Dict[str, List[NormalizedEvent]] = {}
    unknown: List[NormalizedEvent] = []
    for e in events:
        if e.session_key:
            by_session.setdefault(e.session_key, []).append(e)
        else:
            unknown.append(e)

    candidates: List[Tuple[float, str, Optional[str], int]] = []
    # (score, session_key, device_key, delta_ms)
    for sk, evs in by_session.items():
        starts = [x for x in evs if x.kind == "session_start"]
        if not starts:
            continue
        nearest = min(starts, key=lambda x: abs(x.t_event_ms - app_open_event_ms))
        delta = abs(nearest.t_event_ms - app_open_event_ms)
        # Score: higher when delta smaller; cap for stability.
        score = max(0.0, 1.0 - (delta / 30_000.0))
        dk = nearest.device_key
        candidates.append((score, sk, dk, delta))

    candidates.sort(reverse=True, key=lambda x: x[0])

    packed = [
        {"score": s, "session_key": sk, "device_key": dk, "delta_ms": d}
        for (s, sk, dk, d) in candidates[:top_k]
    ]

    if not candidates:
        return ResolutionResult(
            session_key=None,
            device_key=None,
            rationale={
                "reason": "no_session_start_found",
                "note": "Ensure adapter maps the session's first event to kind='session_start'.",
            },
            candidates=packed,
        )

    best_s, best_sk, best_dk, best_delta = candidates[0]
    return ResolutionResult(
        session_key=best_sk,
        device_key=best_dk,
        rationale={
            "method": "log_inference",
            "app_open_video_ms": app_open_video_ms,
            "app_open_event_ms_est": app_open_event_ms,
            "best_delta_ms": best_delta,
            "score": best_s,
        },
        candidates=packed,
    )
