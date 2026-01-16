from __future__ import annotations

from typing import Any, Dict, Optional

from ..models import NormalizedEvent


def basic_normalize(
    *,
    t_event_ms: int,
    kind: str,
    raw: Dict[str, Any],
    session_key: Optional[str] = None,
    device_key: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> NormalizedEvent:
    """Helper to create a NormalizedEvent.

    Keep raw payloads intact; put safe-to-share fields in metadata.
    """

    return NormalizedEvent(
        t_event_ms=t_event_ms,
        kind=kind,
        session_key=session_key,
        device_key=device_key,
        metadata=metadata or {},
        raw=raw,
    )
