from __future__ import annotations

from pathlib import Path

from ..models import FrameRef


def _require_cv2():
    try:
        import cv2  # noqa: F401
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "opencv-python is required to export evidence frames. Install with: pip install -e '.[video]'"
        ) from e


def export_frame(video_path: str | Path, t_video_ms: int, out_dir: str | Path) -> FrameRef:
    """Export a JPEG frame from the video at approximately t_video_ms.

    This is MVP-grade. Exact frame selection depends on codec and container.
    """

    _require_cv2()
    import cv2

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    cap.set(cv2.CAP_PROP_POS_MSEC, float(t_video_ms))
    ok, frame = cap.read()
    cap.release()

    fname = f"frame_{t_video_ms:010d}.jpg"
    out_path = out_dir / fname

    if not ok or frame is None:
        # Create an empty placeholder file so reports still link something.
        out_path.write_bytes(b"")
        return FrameRef(path=str(out_path), t_video_ms=t_video_ms)

    cv2.imwrite(str(out_path), frame)
    return FrameRef(path=str(out_path), t_video_ms=t_video_ms)
