from __future__ import annotations

from typing import Iterable

from .adapter_base import EventAdapter, EventQuery
from ..models import NormalizedEvent


class AthenaAdapter(EventAdapter):
    """Skeleton adapter for AWS Athena.

    This repo intentionally does not include proprietary schemas or SQL.
    Integrators should implement:
    - query construction
    - result parsing
    - normalization to NormalizedEvent

    Recommended: use pyathena and parameterize any source-specific fields...
    """

    def __init__(self, database: str, output_location: str, workgroup: str | None = None) -> None:
        self.database = database
        self.output_location = output_location
        self.workgroup = workgroup

    def fetch(self, q: EventQuery) -> Iterable[NormalizedEvent]:  # pragma: no cover
        raise NotImplementedError(
            "AthenaAdapter.fetch is a skeleton. Provide your SQL + mapping in your environment."
        )
