from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Optional
from urllib.parse import urljoin

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

    Sends IR commands via an HTTP-based IR blaster (e.g., Broadlink RM, Orvibo, etc.).
    Maps RemoteCommand enum to Roku IR codes and transmits via the blaster.

    Supports multiple blaster types via `blaster_type` parameter:
    - 'broadlink': Broadlink RM or similar (HTTP API)
    - 'orvibo': Orvibo AllOne or similar
    - 'custom': Custom HTTP endpoint
    """

    # Roku IR codes (NEC protocol, 32-bit hex)
    # Format: RemoteCommand -> IR code
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
        blaster_type: str = "broadlink",
        timeout_seconds: float = 5.0,
    ) -> None:
        """Initialize Roku IR driver.

        Args:
            ir_blaster_host: IP address or hostname of IR blaster
            ir_blaster_port: HTTP port for IR blaster API (default 80)
            device_id: Device identifier for multi-device blasters (e.g., MAC address)
            blaster_type: Type of IR blaster ('broadlink', 'orvibo', 'custom')
            timeout_seconds: HTTP request timeout
        """
        self.ir_blaster_host = ir_blaster_host
        self.ir_blaster_port = ir_blaster_port
        self.device_id = device_id or "default"
        self.blaster_type = blaster_type
        self.timeout_seconds = timeout_seconds
        self._http_session = None
        self._init_session()

    def _init_session(self) -> None:
        """Initialize HTTP session for communication with IR blaster."""
        try:
            import requests
            self._requests = requests
        except ImportError:
            raise ImportError(
                "requests library is required for RokuIRDriver HTTP communication. "
                "Install with: pip install 'requests>=2.28'"
            )

    def send(self, command: RemoteCommand) -> None:
        """Send IR command to Roku via HTTP-based IR blaster.

        Args:
            command: RemoteCommand to send

        Raises:
            ValueError: If command not supported
            RuntimeError: If HTTP request fails
        """
        if command not in self.ROKU_COMMANDS:
            raise ValueError(f"Unsupported Roku command: {command}")

        ir_code = self.ROKU_COMMANDS[command]
        self._send_via_blaster(ir_code, command)

    def _send_via_blaster(self, ir_code: str, command: RemoteCommand) -> None:
        """Send IR code via appropriate blaster API.

        Args:
            ir_code: Hex IR code to transmit
            command: Remote command for logging/tracking
        """
        if self.blaster_type == "broadlink":
            self._send_broadlink(ir_code, command)
        elif self.blaster_type == "orvibo":
            self._send_orvibo(ir_code, command)
        elif self.blaster_type == "custom":
            self._send_custom(ir_code, command)
        else:
            raise ValueError(f"Unsupported blaster type: {self.blaster_type}")

    def _send_broadlink(self, ir_code: str, command: RemoteCommand) -> None:
        """Send IR code via Broadlink RM API.

        Broadlink devices expose an HTTP API:
        POST /api/irda/send HTTP/1.1
        Content-Type: application/json
        {"device_id": "aabbccddeeff", "code": "0xC23C"}
        """
        url = urljoin(
            f"http://{self.ir_blaster_host}:{self.ir_blaster_port}",
            "/api/irda/send"
        )
        payload = {
            "device_id": self.device_id,
            "code": ir_code,
        }

        try:
            response = self._requests.post(
                url,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            print(
                f"[RokuIRDriver] Sent {command.value} (code={ir_code}) "
                f"to Broadlink {self.ir_blaster_host}"
            )
        except self._requests.RequestException as e:
            raise RuntimeError(
                f"Failed to send IR command to Broadlink {url}: {e}"
            ) from e

    def _send_orvibo(self, ir_code: str, command: RemoteCommand) -> None:
        """Send IR code via Orvibo AllOne API.

        Orvibo devices use a different API format:
        POST /api/irda/send HTTP/1.1
        Content-Type: application/json
        {"code": "0xC23C"}
        """
        url = urljoin(
            f"http://{self.ir_blaster_host}:{self.ir_blaster_port}",
            "/api/irda/send"
        )
        payload = {"code": ir_code}

        try:
            response = self._requests.post(
                url,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            print(
                f"[RokuIRDriver] Sent {command.value} (code={ir_code}) "
                f"to Orvibo {self.ir_blaster_host}"
            )
        except self._requests.RequestException as e:
            raise RuntimeError(
                f"Failed to send IR command to Orvibo {url}: {e}"
            ) from e

    def _send_custom(self, ir_code: str, command: RemoteCommand) -> None:
        """Send IR code via custom HTTP endpoint.

        Expects endpoint at /api/ir/send with JSON payload:
        POST /api/ir/send HTTP/1.1
        Content-Type: application/json
        {"ir_code": "0xC23C", "command": "HOME", "device_id": "device_id"}
        """
        url = urljoin(
            f"http://{self.ir_blaster_host}:{self.ir_blaster_port}",
            "/api/ir/send"
        )
        payload = {
            "ir_code": ir_code,
            "command": command.value,
            "device_id": self.device_id,
        }

        try:
            response = self._requests.post(
                url,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            print(
                f"[RokuIRDriver] Sent {command.value} (code={ir_code}) "
                f"to custom blaster {self.ir_blaster_host}"
            )
        except self._requests.RequestException as e:
            raise RuntimeError(
                f"Failed to send IR command to custom blaster {url}: {e}"
            ) from e


def make_action(command: RemoteCommand, attempt: int = 1) -> Action:
    return Action(t_wall_ms=int(time.time() * 1000), command=command, attempt=attempt)


def make_remote_driver(
    ir_blaster_host: Optional[str],
    ir_blaster_port: int = 80,
    ir_blaster_type: str = "broadlink",
    ir_device_id: Optional[str] = None,
) -> RemoteDriver:
    """Factory function to create appropriate RemoteDriver instance.

    Args:
        ir_blaster_host: IP/hostname of IR blaster (None = LogOnlyDriver)
        ir_blaster_port: HTTP port for IR blaster
        ir_blaster_type: Type of blaster ('broadlink', 'orvibo', 'custom')
        ir_device_id: Device ID for multi-device blasters

    Returns:
        RemoteDriver instance (RokuIRDriver or LogOnlyDriver)
    """
    if ir_blaster_host is None:
        return LogOnlyDriver()

    return RokuIRDriver(
        ir_blaster_host=ir_blaster_host,
        ir_blaster_port=ir_blaster_port,
        device_id=ir_device_id,
        blaster_type=ir_blaster_type,
    )
