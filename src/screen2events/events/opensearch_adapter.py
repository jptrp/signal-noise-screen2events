from __future__ import annotations

from typing import Iterable, Optional

from .adapter_base import EventAdapter, EventQuery
from ..models import NormalizedEvent


class OpenSearchAdapter(EventAdapter):
    """OpenSearch adapter for fetching telemetry events.

    This adapter queries an OpenSearch cluster and normalizes results to NormalizedEvent.
    It assumes:
    - timestamp field in milliseconds (or will convert if in seconds)
    - event_type or kind field for event classification
    - optional device_id/device_key and session_id/session_key fields
    """

    def __init__(
        self,
        host: str,
        index: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        try:
            from opensearchpy import OpenSearch
        except ImportError:
            raise ImportError(
                "opensearch-py is required for OpenSearchAdapter. "
                "Install with: pip install 'opensearch-py>=2.4'"
            )

        self.host = host
        self.index = index
        auth = None
        if username and password:
            auth = (username, password)

        self.client = OpenSearch(
            hosts=[{"host": host, "port": 9200}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=False,
        )

    def fetch(self, q: EventQuery) -> Iterable[NormalizedEvent]:
        """Query OpenSearch for events in time range and normalize them.

        Args:
            q: EventQuery with time bounds, optional device_key and session_key

        Yields:
            NormalizedEvent objects
        """
        # Build query: time range is mandatory
        must_clauses = [
            {
                "range": {
                    "timestamp": {
                        "gte": q.time_start_ms,
                        "lte": q.time_end_ms,
                    }
                }
            }
        ]

        # Optional device filter
        if q.device_key:
            must_clauses.append({"term": {"device_id": q.device_key}})

        # Optional session filter
        if q.session_key:
            must_clauses.append({"term": {"session_id": q.session_key}})

        query_body = {
            "query": {"bool": {"must": must_clauses}},
            "size": q.limit or 1000,
            "sort": [{"timestamp": {"order": "asc"}}],
        }

        try:
            response = self.client.search(index=self.index, body=query_body)
        except Exception as e:
            raise RuntimeError(f"OpenSearch query failed: {e}") from e

        for hit in response.get("hits", {}).get("hits", []):
            doc = hit["_source"]
            yield self._normalize(doc)

    def _normalize(self, doc: dict) -> NormalizedEvent:
        """Convert OpenSearch document to NormalizedEvent.

        Adapts common field name variations (timestamp/ts, event_type/kind, etc.).
        """
        # Extract and normalize timestamp (assume ms)
        t_ms = doc.get("timestamp") or doc.get("ts") or 0
        if isinstance(t_ms, float) and t_ms < 10**10:  # Likely in seconds
            t_ms = int(t_ms * 1000)
        else:
            t_ms = int(t_ms)

        # Extract event kind
        kind = doc.get("event_type") or doc.get("kind") or "unknown"

        # Extract identifiers
        session_key = doc.get("session_id") or doc.get("session_key")
        device_key = doc.get("device_id") or doc.get("device_key")

        # Safe metadata (non-sensitive fields)
        metadata = {
            "user_id": doc.get("user_id"),
            "content_id": doc.get("content_id"),
            "content_title": doc.get("content_title"),
            "player_state": doc.get("player_state"),
            "quality": doc.get("quality"),
            "bandwidth_mbps": doc.get("bandwidth_mbps"),
        }
        # Remove None values
        metadata = {k: v for k, v in metadata.items() if v is not None}

        return NormalizedEvent(
            t_event_ms=t_ms,
            kind=kind,
            session_key=session_key,
            device_key=device_key,
            metadata=metadata,
            raw=doc,  # Store full doc for debugging
        )
