from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from ..models import Alignment, Finding


def render_report_md(
    *,
    out_path: str | Path,
    run_id: str,
    video_path: str,
    alignment: Alignment,
    findings: List[Finding],
    notes: Optional[str] = None,
) -> None:
    p = Path(out_path)
    lines: List[str] = []
    lines.append("# Screen-to-Events Correlation Report")
    lines.append("")
    lines.append(f"- Run: `{run_id}`")
    lines.append(f"- Video: `{video_path}`")
    lines.append(f"- Alignment: offset_ms={alignment.offset_ms}, drift_ppm={alignment.drift_ppm}, score={alignment.score:.2f}")
    lines.append("")

    if notes:
        lines.append("## Notes")
        lines.append(notes)
        lines.append("")

    lines.append("## Findings")
    if not findings:
        lines.append("No findings. (That may mean you haven't mapped any event kinds yet.)")
        lines.append("")
    else:
        for f in findings:
            lines.append(f"### [{f.severity.upper()}] {f.title}")
            lines.append("")
            lines.append(f.description)
            lines.append("")
            if f.t_video_ms is not None or f.t_event_ms is not None:
                lines.append("**Timing**")
                if f.t_video_ms is not None:
                    lines.append(f"- t_video_ms: `{f.t_video_ms}`")
                if f.t_event_ms is not None:
                    lines.append(f"- t_event_ms: `{f.t_event_ms}`")
                lines.append("")

            if f.evidence_frames:
                lines.append("**Evidence frames**")
                for fr in f.evidence_frames:
                    rel = fr.path
                    lines.append(f"- `{rel}` (t_video_ms={fr.t_video_ms})")
                lines.append("")

            if f.details:
                lines.append("<details><summary>Details</summary>")
                lines.append("")
                for k, v in f.details.items():
                    lines.append(f"- **{k}**: `{v}`")
                lines.append("")
                lines.append("</details>")
                lines.append("")

    p.write_text("\n".join(lines), encoding="utf-8")
