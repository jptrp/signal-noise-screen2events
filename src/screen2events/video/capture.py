from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional, Tuple


@dataclass(frozen=True)
class VideoFrame:
    """A single decoded frame.

    `image` is an OpenCV BGR ndarray.
    """

    t_video_ms: int
    image: object  # ndarray


def _require_cv2():
    try:
        import cv2  # noqa: F401
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "opencv-python is required for video capture. Install with: pip install -e '.[video]'"
        ) from e


def open_video(path: str | Path):
    _require_cv2()
    import cv2

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {path}")
    return cap


def iter_frames(
    cap,
    sample_fps: float = 10.0,
    max_frames: Optional[int] = None,
) -> Iterator[VideoFrame]:
    """Iterate frames from an OpenCV VideoCapture at approximately sample_fps.

    This is an MVP sampler. For precise timing, upgrade to track PTS/DTS.
    """

    _require_cv2()
    import cv2

    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    step = max(int(round(src_fps / sample_fps)), 1)

    frame_idx = 0
    yielded = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break

        if frame_idx % step == 0:
            t_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))
            yield VideoFrame(t_video_ms=t_ms, image=frame)
            yielded += 1
            if max_frames is not None and yielded >= max_frames:
                break

        frame_idx += 1


def get_video_shape(cap) -> Tuple[int, int]:
    """Return (width, height)."""
    _require_cv2()
    import cv2

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    return w, h
