from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from ..models import Observation, UXState
from .detectors import DetectorConfig, classify_state
from .motion import MotionTracker


@dataclass
class StateMachineConfig:
    sample_fps: float = 10.0
    detector: DetectorConfig = field(default_factory=DetectorConfig)
    enable_ocr: bool = False
    ocr_roi_norm: Optional[tuple[float, float, float, float]] = None


class VisionStateMachine:
    """MVP vision-driven state machine.

    This is intentionally simple and explainable.
    """

    def __init__(self, cfg: StateMachineConfig) -> None:
        self.cfg = cfg
        self.motion = MotionTracker()
        self._last_state: UXState = UXState.UNKNOWN

        self._ocr_fn = None
        self._ocr_cfg = None
        if cfg.enable_ocr:
            from .ocr import OCRConfig, ocr_text

            self._ocr_fn = ocr_text
            self._ocr_cfg = OCRConfig(roi_norm=cfg.ocr_roi_norm)

    def observe(self, t_video_ms: int, frame_bgr) -> Observation:
        signals = {}

        m = self.motion.update(frame_bgr)
        if m is not None:
            signals["motion"] = m

        text = None
        if self._ocr_fn is not None:
            try:
                text = self._ocr_fn(frame_bgr, self._ocr_cfg)
            except Exception:
                # OCR is optional; failures shouldn't break the run.
                text = None
        if text:
            signals["ocr_text"] = text

        state = classify_state(signals, self.cfg.detector)
        # Confidence heuristic: known states are higher-confidence than UNKNOWN.
        conf = 0.85 if state != UXState.UNKNOWN else 0.35

        self._last_state = state
        return Observation(t_video_ms=t_video_ms, state=state, confidence=conf, signals=signals, ocr_text=text)


def observations_from_video(path: str, cfg: StateMachineConfig, max_frames: int | None = None) -> List[Observation]:
    """Convenience helper: open a video file and produce observations."""

    from .capture import iter_frames, open_video

    cap = open_video(path)
    sm = VisionStateMachine(cfg)

    obs: List[Observation] = []
    for vf in iter_frames(cap, sample_fps=cfg.sample_fps, max_frames=max_frames):
        obs.append(sm.observe(vf.t_video_ms, vf.image))
    cap.release()
    return obs
