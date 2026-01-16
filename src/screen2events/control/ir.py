from __future__ import annotations

import time
from abc import ABC, abstractmethod

from ..models import Action, RemoteCommand


class RemoteDriver(ABC):
    """Abstract remote control driver.

    Implementations can target:
    - network IR blasters
    - USB IR transmitters
    - manual/human-in-the-loop (log-only)

    The system never assumes a command succeeded until the vision pipeline
    confirms a state change.
    """

    @abstractmethod
    def send(self, command: RemoteCommand) -> None:
        raise NotImplementedError


class LogOnlyDriver(RemoteDriver):
    """A no-op driver used when you don't yet have IR hardware.

    This is useful for early prototyping: you can manually drive the remote,
    and still record actions in the run artifacts.
    """

    def send(self, command: RemoteCommand) -> None:  # pragma: no cover
        # No-op. Intentional.
        return


def make_action(command: RemoteCommand, attempt: int = 1) -> Action:
    return Action(t_wall_ms=int(time.time() * 1000), command=command, attempt=attempt)
