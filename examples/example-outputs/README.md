# Example Outputs

This directory contains sample outputs from a typical Screen-to-Events run. Use these to understand what success looks like.

## Contents

- **report.md** — Human-readable summary with findings and evidence
- **observations.jsonl** — Screen-derived state timeline
- **events.jsonl** — Telemetry-derived event timeline  
- **findings.jsonl** — Mismatches and anomalies detected
- **alignment.json** — Time offset and drift model

## Sample Scenario

A 5-minute Roku Home/Live TV session:
1. Home screen → browse live TV → start playback
2. Watch for 2 minutes → buffering event → resume
3. Ad interrupt → skip ad → resume playback
4. Pause → settings menu → back to playback
5. Stop playback

This produced:
- 10 telemetry events
- 300 video observations (at 1 frame/sec sampling)
- 2 findings (minor timing mismatches)
- Timeline alignment: ±50ms offset, 0.1% drift

## How to Generate Your Own

```bash
s2e run --config examples/config.example.yaml --video session.mp4 --out runs
```

Output is written to `runs/<timestamp>/` with the same structure as these examples.

## Interpreting Results

See [../docs/for-data-teams.md](../docs/for-data-teams.md) for detailed interpretation guides.
