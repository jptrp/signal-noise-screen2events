from __future__ import annotations

from collections import Counter
from typing import Dict, List

from ..models import Finding, FindingSeverity


def findings_from_matches(matches: List[Dict[str, object]]) -> List[Finding]:
    findings: List[Finding] = []
    counts = Counter([m.get("event_kind") for m in matches])

    # Flag mismatches
    for m in matches:
        if m.get("match") is True:
            continue
        findings.append(
            Finding(
                severity=FindingSeverity.WARN,
                title=f"Mismatch: {m.get('event_kind')}",
                description=(
                    f"Expected screen state `{m.get('expected_state')}` but saw `{m.get('obs_state')}`. "
                    f"Delta={m.get('delta_ms')}ms"
                ),
                t_video_ms=int(m.get("obs_time_ms") or 0),
                t_event_ms=int(m.get("event_time_ms") or 0),
                details={k: v for k, v in m.items() if k not in {"raw"}},
            )
        )

    # Very small sanity checks (generic)
    if counts.get("playback", 0) == 0:
        findings.append(
            Finding(
                severity=FindingSeverity.INFO,
                title="No playback events matched",
                description="No events of kind 'playback' were matched to screen playback state. This may be expected if your adapter does not emit that kind yet.",
            )
        )

    return findings
