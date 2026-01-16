from __future__ import annotations

from typing import Iterable

from .adapter_base import EventAdapter, EventQuery
from ..models import NormalizedEvent


class OpenSearchAdapter(EventAdapter):
    """Skeleton adapter for OpenSearch.

    This repo intentionally avoids assuming index names or document shapes.
    Integrators should implement:
    - query DSL construction
    - scrolling/pagination
    - normalization to NormalizedEvent
    """

    def __init__(self, host: str, index: str, auth: tuple[str, str] | None = None) -> None:
        self.host = host
        self.index = index
        self.auth = auth

    def fetch(self, q: EventQuery) -> Iterable[NormalizedEvent]:  # pragma: no cover
        raise NotImplementedError(
            "OpenSearchAdapter.fetch is a skeleton. Provide your query + mapping in your environment."
        )
