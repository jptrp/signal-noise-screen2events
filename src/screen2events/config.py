from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class VideoConfig(BaseModel):
    sample_fps: float = 10.0
    enable_ocr: bool = False
    ocr_roi_norm: Optional[tuple[float, float, float, float]] = None


class TelemetryConfig(BaseModel):
    # Use 'file' for public demo (events.jsonl of NormalizedEvent)
    adapter: str = Field("file", description="file|athena|opensearch")
    events_file: Optional[str] = None
    # OpenSearch adapter configuration
    opensearch_host: Optional[str] = None
    opensearch_index: Optional[str] = None
    opensearch_username: Optional[str] = None
    opensearch_password: Optional[str] = None


class RunConfig(BaseModel):
    run_id: str = "run"
    # If you can't detect APP_OPEN yet, set this explicitly.
    app_open_video_ms: Optional[int] = None
    # Optional stable device identity to filter telemetry
    device_key: Optional[str] = None
    video: VideoConfig = VideoConfig()
    telemetry: TelemetryConfig = TelemetryConfig()
    # Optional IR blaster configuration
    ir_blaster_host: Optional[str] = None
    ir_blaster_port: int = 80
    ir_blaster_type: str = "broadlink"  # broadlink, orvibo, custom
    ir_device_id: Optional[str] = None


def load_config(path: str | Path) -> RunConfig:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return RunConfig.model_validate(data)
