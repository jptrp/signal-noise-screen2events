from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Optional

from ..models import NormalizedEvent


@dataclass
class EventQuery:
    """Generic event query.

    This repo avoids assumptions about schema. Adapters interpret these fields
    in a source-appropriate way.
    """

    time_start_ms: int
    time_end_ms: int
    device_key: Optional[str] = None
    session_key: Optional[str] = None
    limit: Optional[int] = None


class EventAdapter(ABC):
    """Read events from some source and normalize them."""

    @abstractmethod
    def fetch(self, q: EventQuery) -> Iterable[NormalizedEvent]:
        raise NotImplementedError
