from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional

from ..models import Action, Observation, RemoteCommand, UXState
from .ir import RemoteDriver, make_action


@dataclass
class VerifyConfig:
    timeout_s: float = 5.0
    poll_interval_s: float = 0.2


def send_and_verify(
    driver: RemoteDriver,
    command: RemoteCommand,
    get_latest_observation: Callable[[], Optional[Observation]],
    expected_state: Optional[UXState] = None,
    cfg: VerifyConfig = VerifyConfig(),
) -> Action:
    """Send a command and verify via vision.

    get_latest_observation should return the most recent Observation available.
    This is designed for near-real-time loops; for offline playback, verification
    can be performed by analyzing observations around an action timestamp.
    """

    action = make_action(command)
    driver.send(command)

    if expected_state is None:
        return action

    deadline = time.time() + cfg.timeout_s
    last = None
    while time.time() < deadline:
        obs = get_latest_observation()
        if obs is not None:
            last = obs
            if obs.state == expected_state:
                action.verified = True
                action.verification = {"state": obs.state, "t_video_ms": obs.t_video_ms}
                return action
        time.sleep(cfg.poll_interval_s)

    action.verified = False
    action.verification = {
        "expected_state": expected_state,
        "last_seen": (last.state if last else None),
        "last_t_video_ms": (last.t_video_ms if last else None),
    }
    return action
