from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UXState(str, Enum):
    UNKNOWN = "unknown"
    HOME = "home"
    APP_OPEN = "app_open"
    BROWSE = "browse"
    PLAYBACK = "playback"
    BUFFERING = "buffering"
    AD = "ad"
    PAUSED = "paused"
    ERROR = "error"


class FrameRef(BaseModel):
    """Reference to a frame exported from the video."""

    path: str
    t_video_ms: int


class Observation(BaseModel):
    """A single screen-derived observation produced by the vision/state machine."""

    t_video_ms: int = Field(..., ge=0)
    state: UXState = UXState.UNKNOWN
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    signals: Dict[str, Any] = Field(default_factory=dict)
    ocr_text: Optional[str] = None
    frame: Optional[FrameRef] = None


class RemoteCommand(str, Enum):
    HOME = "HOME"
    BACK = "BACK"
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    SELECT = "SELECT"
    PLAY_PAUSE = "PLAY_PAUSE"


class Action(BaseModel):
    """A remote-control action (IR or manual) and its verification result."""

    t_wall_ms: int = Field(..., ge=0)
    command: RemoteCommand
    attempt: int = Field(1, ge=1)
    verified: bool = False
    verification: Dict[str, Any] = Field(default_factory=dict)


class NormalizedEvent(BaseModel):
    """A vendor-agnostic normalized telemetry event.

    This intentionally avoids assuming proprietary field names.
    Adapters should store raw payloads and expose safe-to-share metadata.
    """

    t_event_ms: int = Field(..., ge=0)
    kind: str = Field(..., description="Coarse event kind (e.g., session_start, state, error, heartbeat)")
    session_key: Optional[str] = Field(None, description="Ephemeral session/visit identifier, if available")
    device_key: Optional[str] = Field(None, description="Stable device identifier, if available")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    raw: Dict[str, Any] = Field(default_factory=dict)


class Alignment(BaseModel):
    """Alignment between video time and event time.

    offset_ms: add to video_ms to estimate event_ms (event_ms ~= video_ms + offset_ms)
    """

    offset_ms: int = 0
    drift_ppm: float = 0.0
    anchors: List[Dict[str, Any]] = Field(default_factory=list)
    score: float = 0.0


class FindingSeverity(str, Enum):
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


class Finding(BaseModel):
    """A correlation finding backed by evidence."""

    severity: FindingSeverity
    title: str
    description: str
    t_video_ms: Optional[int] = None
    t_event_ms: Optional[int] = None
    evidence_frames: List[FrameRef] = Field(default_factory=list)
    related_events: List[NormalizedEvent] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)
