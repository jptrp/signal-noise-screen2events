from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

from ..models import Alignment, NormalizedEvent, Observation, UXState


@dataclass
class MatchConfig:
    """Configuration for coarse event<->state matching.

    Because this repo is schema-agnostic, we keep mapping based on the normalized
    event.kind.
    """

    max_delta_ms: int = 5_000
    kind_to_state: Dict[str, UXState] = field(
        default_factory=lambda: {
            "playback": UXState.PLAYBACK,
            "buffering": UXState.BUFFERING,
            "ad": UXState.AD,
            "pause": UXState.PAUSED,
            "error": UXState.ERROR,
        }
    )


def _nearest_observation(observations: List[Observation], t_video_ms: int) -> Tuple[Optional[Observation], int]:
    if not observations:
        return None, 1_000_000_000
    best = min(observations, key=lambda o: abs(o.t_video_ms - t_video_ms))
    return best, abs(best.t_video_ms - t_video_ms)


def match_events_to_screen(
    *,
    observations: List[Observation],
    events: Iterable[NormalizedEvent],
    alignment: Alignment,
    cfg: MatchConfig = MatchConfig(),
) -> List[Dict[str, object]]:
    """Return coarse matches between normalized events and screen states.

    For each event with a kind mapped to a UXState, compute the expected video
    timestamp and match to the nearest observation.
    """

    matches: List[Dict[str, object]] = []
    for e in events:
        expected_state = cfg.kind_to_state.get(e.kind)
        if expected_state is None:
            continue

        # Convert event time -> estimated video time
        t_video_est = int(e.t_event_ms - alignment.offset_ms)
        obs, delta = _nearest_observation(observations, t_video_est)
        if obs is None:
            continue

        ok = delta <= cfg.max_delta_ms and obs.state == expected_state
        matches.append(
            {
                "event_kind": e.kind,
                "event_time_ms": e.t_event_ms,
                "video_time_est_ms": t_video_est,
                "obs_time_ms": obs.t_video_ms,
                "obs_state": obs.state,
                "expected_state": expected_state,
                "delta_ms": delta,
                "match": ok,
                "session_key": e.session_key,
                "device_key": e.device_key,
            }
        )

    return matches
