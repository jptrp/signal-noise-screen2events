from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Optional

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


class RokuIRDriver(RemoteDriver):
    """IR driver for Roku devices.

    Sends IR commands via an HTTP-based IR blaster (e.g., Broadlink RM, etc.).
    Maps RemoteCommand enum to Roku IR codes and transmits via the blaster.
    """

    # Roku IR codes (hex strings, manufacturer-specific)
    ROKU_COMMANDS = {
        RemoteCommand.HOME: "0xC23C",
        RemoteCommand.BACK: "0x3C3C",
        RemoteCommand.UP: "0x10EF",
        RemoteCommand.DOWN: "0x00FF",
        RemoteCommand.LEFT: "0x7E81",
        RemoteCommand.RIGHT: "0x3EC1",
        RemoteCommand.SELECT: "0x20DF",
        RemoteCommand.PLAY_PAUSE: "0x807F",
    }

    def __init__(
        self,
        ir_blaster_host: str,
        ir_blaster_port: int = 80,
        device_id: Optional[str] = None,
    ) -> None:
        """Initialize Roku IR driver.

        Args:
            ir_blaster_host: IP address or hostname of IR blaster
            ir_blaster_port: HTTP port for IR blaster API (default 80)
            device_id: Optional device identifier for multi-device blasters
        """
        self.ir_blaster_host = ir_blaster_host
        self.ir_blaster_port = ir_blaster_port
        self.device_id = device_id or "default"

    def send(self, command: RemoteCommand) -> None:
        """Send IR command to Roku via blaster.

        This is a stub that logs the command. For actual use, implement:
        - HTTP POST to IR blaster API
        - Or use LIRC (Linux IR Control) if available
        - Or use specific blaster library (e.g., broadlink, etc.)
        """
        if command not in self.ROKU_COMMANDS:
            raise ValueError(f"Unsupported Roku command: {command}")

        ir_code = self.ROKU_COMMANDS[command]
        # TODO: Send IR code via HTTP to blaster
        # Example for Broadlink RM:
        # POST http://{ir_blaster_host}:{ir_blaster_port}/api/ir/send
        # Body: {"device_id": self.device_id, "ir_code": ir_code}
        print(f"[RokuIRDriver] Would send {command.value} -> {ir_code} to {self.ir_blaster_host}")


def make_action(command: RemoteCommand, attempt: int = 1) -> Action:
    return Action(t_wall_ms=int(time.time() * 1000), command=command, attempt=attempt)
