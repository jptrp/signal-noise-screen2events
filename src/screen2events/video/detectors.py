from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from ..models import UXState


@dataclass
class DetectorConfig:
    # Motion thresholds are intentionally conservative defaults.
    playback_motion_min: float = 0.03
    paused_motion_max: float = 0.01


def classify_state(signals: Dict[str, object], cfg: DetectorConfig) -> UXState:
    """Coarse classification from signals.

    This is deliberately simple for the MVP. You can extend it with:
    - OCR tokens (e.g., "Error", "Loading", "Skip")
    - logo/template matching
    - spinner detectors
    - UI layout signatures
    """

    ocr = (signals.get("ocr_text") or "").lower()
    motion = float(signals.get("motion") or 0.0)

    # Error cues
    if "error" in ocr or "try again" in ocr:
        return UXState.ERROR

    # Buffering cues
    if "loading" in ocr or "buffer" in ocr:
        return UXState.BUFFERING

    # Ad cues
    if "skip" in ocr and "ad" in ocr:
        return UXState.AD

    # Playback vs paused by motion
    if motion >= cfg.playback_motion_min:
        return UXState.PLAYBACK
    if motion <= cfg.paused_motion_max:
        return UXState.PAUSED

    return UXState.UNKNOWN
