from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


def _require_ocr():
    try:
        import pytesseract  # noqa: F401
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "pytesseract is required for OCR. Install with: pip install -e '.[video]'. "
            "You may also need to install the system tesseract binary."
        ) from e


@dataclass
class OCRConfig:
    # ROI as normalized coords: (x1, y1, x2, y2)
    roi_norm: Optional[Tuple[float, float, float, float]] = None


def ocr_text(frame_bgr, cfg: OCRConfig) -> str:
    _require_ocr()
    import pytesseract

    # Lazy import cv2 only when OCR is used.
    import cv2

    img = frame_bgr
    if cfg.roi_norm is not None:
        h, w = img.shape[:2]
        x1, y1, x2, y2 = cfg.roi_norm
        px1 = int(max(0, min(w, x1 * w)))
        py1 = int(max(0, min(h, y1 * h)))
        px2 = int(max(0, min(w, x2 * w)))
        py2 = int(max(0, min(h, y2 * h)))
        img = img[py1:py2, px1:px2]

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    text = pytesseract.image_to_string(gray)
    return " ".join(text.split())
