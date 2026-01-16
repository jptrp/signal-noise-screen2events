from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .config import load_config
from .correlate.align import estimate_offset_from_session_start
from .correlate.match import match_events_to_screen
from .correlate.anomalies import findings_from_matches
from .events.adapter_base import EventQuery
from .events.file_adapter import FileAdapter
from .models import Alignment, Finding, Observation, UXState
from .report.evidence import export_frame
from .report.render_md import render_report_md
from .utils import ensure_dir, write_json, write_jsonl
from .video.state_machine import StateMachineConfig, observations_from_video

app = typer.Typer(add_completion=False)
console = Console()


def _mk_run_dir(base: Path) -> Path:
    ts = time.strftime("%Y%m%d_%H%M%S")
    out = base / ts
    out.mkdir(parents=True, exist_ok=True)
    return out


def _detect_app_open(obs: list[Observation]) -> int:
    for o in obs:
        if o.state == UXState.APP_OPEN:
            return o.t_video_ms
    # Fallback: first observation is used as the gate point.
    return obs[0].t_video_ms if obs else 0


@app.command()
def run(
    config: str = typer.Option(..., "--config", "-c", help="Path to YAML config"),
    video: str = typer.Option(..., "--video", "-v", help="Path to video file (mp4/mkv/etc.)"),
    out_base: str = typer.Option("runs", "--out", help="Output directory base"),
    max_frames: Optional[int] = typer.Option(None, "--max-frames", help="Limit frames for quick tests"),
):
    """Analyze a video session and correlate it with normalized telemetry events."""

    cfg = load_config(config)
    out_dir = _mk_run_dir(Path(out_base))

    console.print(f"[bold]Run[/bold] {cfg.run_id} -> {out_dir}")

    # 1) Vision observations
    sm_cfg = StateMachineConfig(
        sample_fps=cfg.video.sample_fps,
        enable_ocr=cfg.video.enable_ocr,
        ocr_roi_norm=cfg.video.ocr_roi_norm,
    )
    console.print("[cyan]Analyzing video...[/cyan]")
    observations = observations_from_video(video, sm_cfg, max_frames=max_frames)
    write_jsonl(out_dir / "observations.jsonl", observations)

    if not observations:
        raise typer.Exit(code=2)

    # 2) Gate point for telemetry
    app_open_video_ms = cfg.app_open_video_ms if cfg.app_open_video_ms is not None else _detect_app_open(observations)
    write_json(out_dir / "gate.json", {"app_open_video_ms": app_open_video_ms})

    # 3) Telemetry (file or opensearch)
    events = []
    if cfg.telemetry.adapter == "file":
        if not cfg.telemetry.events_file:
            console.print("[yellow]No telemetry events file provided. Skipping event correlation.[/yellow]")
        else:
            adapter = FileAdapter(cfg.telemetry.events_file)
            q = EventQuery(
                time_start_ms=app_open_video_ms,
                time_end_ms=app_open_video_ms + 300_000,
                device_key=cfg.device_key,
            )
            events = list(adapter.fetch(q))
            write_jsonl(out_dir / "events.jsonl", events)
    elif cfg.telemetry.adapter == "opensearch":
        from .events.opensearch_adapter import OpenSearchAdapter

        if not cfg.telemetry.opensearch_host or not cfg.telemetry.opensearch_index:
            console.print(
                "[yellow]OpenSearch adapter requires opensearch_host and opensearch_index."
                " Skipping event correlation.[/yellow]"
            )
        else:
            try:
                adapter = OpenSearchAdapter(
                    host=cfg.telemetry.opensearch_host,
                    index=cfg.telemetry.opensearch_index,
                    username=cfg.telemetry.opensearch_username,
                    password=cfg.telemetry.opensearch_password,
                )
                q = EventQuery(
                    time_start_ms=app_open_video_ms,
                    time_end_ms=app_open_video_ms + 300_000,
                    device_key=cfg.device_key,
                )
                events = list(adapter.fetch(q))
                write_jsonl(out_dir / "events.jsonl", events)
                console.print(f"[cyan]Fetched {len(events)} events from OpenSearch.[/cyan]")
            except Exception as e:
                console.print(f"[red]OpenSearch fetch failed: {e}[/red]")
    else:
        console.print(
            "[yellow]Telemetry adapter type not recognized. Use file or opensearch.[/yellow]"
        )

    # 4) Alignment + correlation
    alignment: Alignment = Alignment(offset_ms=0, drift_ppm=0.0, anchors=[], score=0.0)
    findings: list[Finding] = []

    if events:
        alignment = estimate_offset_from_session_start(app_open_video_ms=app_open_video_ms, events=events)
        write_json(out_dir / "alignment.json", alignment.model_dump())

        matches = match_events_to_screen(observations=observations, events=events, alignment=alignment)
        write_json(out_dir / "matches.json", matches)

        findings = findings_from_matches(matches)

        # Export evidence frames for findings that have t_video_ms
        evidence_dir = ensure_dir(out_dir / "evidence")
        for f in findings:
            if f.t_video_ms is not None and f.t_video_ms > 0:
                fr = export_frame(video, f.t_video_ms, evidence_dir)
                f.evidence_frames.append(fr)

    # 5) Report
    render_report_md(
        out_path=out_dir / "report.md",
        run_id=cfg.run_id,
        video_path=video,
        alignment=alignment,
        findings=findings,
        notes=(
            "This is an MVP report. Vision detectors and event normalization are intentionally generic.\n"
            "Refine detectors, add anchor points, and map normalized event kinds to your telemetry."
        ),
    )

    console.print("[green]Done.[/green]")
    console.print(f"Report: {out_dir / 'report.md'}")


if __name__ == "__main__":
    app()
