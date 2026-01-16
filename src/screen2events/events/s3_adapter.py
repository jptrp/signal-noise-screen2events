from __future__ import annotations

import json
from typing import Iterable, Optional

import botocore
import boto3

from .adapter_base import EventAdapter, EventQuery
from ..models import NormalizedEvent


class S3Adapter(EventAdapter):
    """Read JSONL event files from S3 and yield NormalizedEvent instances.

    Expect each object to contain newline-delimited JSON records. Records should
    already conform to the `NormalizedEvent` shape (preferred). Adapter will
    attempt to validate records and skip any invalid lines with a warning.
    """

    def __init__(self, bucket: str, prefix: Optional[str] = None, region: Optional[str] = None, profile: Optional[str] = None):
        self.bucket = bucket
        self.prefix = prefix or ""
        if profile:
            session = boto3.Session(profile_name=profile, region_name=region)
        else:
            session = boto3.Session(region_name=region)
        self.s3 = session.client("s3")

    def _list_keys(self) -> Iterable[str]:
        paginator = self.s3.get_paginator("list_objects_v2")
        kwargs = {"Bucket": self.bucket, "Prefix": self.prefix} if self.prefix else {"Bucket": self.bucket}
        for page in paginator.paginate(**kwargs):
            for obj in page.get("Contents", []):
                yield obj["Key"]

    def _stream_object_lines(self, key: str) -> Iterable[str]:
        try:
            resp = self.s3.get_object(Bucket=self.bucket, Key=key)
            body = resp["Body"]
            for raw in body.iter_lines():
                if raw:
                    yield raw.decode("utf-8")
        except botocore.exceptions.ClientError as e:
            # Surface the error as an exception to the caller
            raise

    def fetch(self, q: EventQuery) -> Iterable[NormalizedEvent]:
        # Simple strategy: read all objects under prefix and yield any parsed events.
        for key in self._list_keys():
            for line in self._stream_object_lines(key):
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                try:
                    # If the JSON already matches NormalizedEvent, validate it.
                    ev = NormalizedEvent.model_validate(obj)
                except Exception:
                    # Try a best-effort mapping for common shapes
                    # Expecting at least t_event_ms and kind
                    t = obj.get("t_event_ms") or obj.get("timestamp_ms") or obj.get("ts")
                    kind = obj.get("kind") or obj.get("type") or obj.get("event")
                    if t is None or kind is None:
                        continue
                    try:
                        ev = NormalizedEvent(
                            t_event_ms=int(t),
                            kind=str(kind),
                            session_key=obj.get("session_key"),
                            device_key=obj.get("device_key"),
                            metadata=obj.get("metadata") or {},
                            raw=obj,
                        )
                    except Exception:
                        continue
                # Apply simple time-range filter if available
                if q.time_start_ms is not None and ev.t_event_ms < q.time_start_ms:
                    continue
                if q.time_end_ms is not None and ev.t_event_ms > q.time_end_ms:
                    continue
                if q.device_key and ev.device_key and ev.device_key != q.device_key:
                    continue
                yield ev
