from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .adapter_base import EventAdapter, EventQuery
from ..models import NormalizedEvent
from ..utils import read_jsonl


class FileAdapter(EventAdapter):
    """Read normalized events from a JSONL file.

    Each line must be a NormalizedEvent JSON object.

    This is the easiest way to integrate publicly without exposing internal schemas.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def fetch(self, q: EventQuery) -> Iterable[NormalizedEvent]:
        for e in read_jsonl(self.path, NormalizedEvent):
            if e.t_event_ms < q.time_start_ms or e.t_event_ms > q.time_end_ms:
                continue
            if q.device_key and e.device_key != q.device_key:
                continue
            if q.session_key and e.session_key != q.session_key:
                continue
            yield e
