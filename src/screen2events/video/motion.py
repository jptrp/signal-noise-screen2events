from __future__ import annotations

from typing import Optional


def _require_cv2():
    try:
        import cv2  # noqa: F401
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "opencv-python is required for motion scoring. Install with: pip install -e '.[video]'"
        ) from e


def motion_score(prev_bgr, curr_bgr, downscale: int = 4) -> float:
    """Return a simple [0,1] motion score between two frames.

    MVP heuristic:
    - convert to grayscale
    - downscale for speed
    - mean absolute difference normalized to 255
    """

    _require_cv2()
    import cv2

    def prep(img):
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if downscale > 1:
            g = cv2.resize(g, (g.shape[1] // downscale, g.shape[0] // downscale))
        return g

    a = prep(prev_bgr)
    b = prep(curr_bgr)
    diff = cv2.absdiff(a, b)
    return float(diff.mean() / 255.0)


class MotionTracker:
    """Stateful motion tracker."""

    def __init__(self) -> None:
        self._prev = None

    def update(self, frame_bgr) -> Optional[float]:
        if self._prev is None:
            self._prev = frame_bgr
            return None
        score = motion_score(self._prev, frame_bgr)
        self._prev = frame_bgr
        return score
