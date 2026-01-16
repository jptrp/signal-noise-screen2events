# For Data Teams — Quick Integration Guide

This brief guide helps data/insights teams evaluate and integrate with the Screen-&-Events correlator.

Why it matters
- Correlate user-visible states (video-derived) with telemetry to detect mismatches, missing events, or optimistic telemetry.
- Useful for QA, RCA, SLA verification, and telemetry quality monitoring.

Core fields (NormalizedEvent)
- `t_event_ms` (int): event timestamp in milliseconds
- `kind` (str): coarse event kind (e.g., session_start, playback, buffering, ad, error)
- `session_key` (str|null): ephemeral session/visit id if available
- `device_key` (str|null): stable device id if available
- `metadata` (dict): safe-to-share attributes

Quickstarts
- S3 (recommended demo): write newline-delimited JSON (`NormalizedEvent`) to S3 and point the CLI at `examples/s3_config.yaml`.
- Athena: use `examples/athena_queries.sql` to map raw logs into the `NormalizedEvent` projection.
- OpenSearch: use the OpenSearch adapter for observability stacks; see `examples/roku_config.yaml`.

Example KPIs to compute
- Match Rate: fraction of telemetry events matched to a screen observation
- Median Telemetry Latency: median(event_time - estimated_video_time)
- Missing Events: events claimed but not observed (by kind)
- False Positives: visual observations with no corresponding telemetry claim

Integration patterns
- Offline batch (S3): easiest to reproduce; upload JSONL to S3 and run `s2e run --config examples/s3_config.yaml`.
- SQL-backed (Athena): run scheduled queries to produce normalized JSONL and export to S3.
- Search-backed (OpenSearch): great for near-real-time queries; use offsets and time windows.

Best practices
- Normalize timestamps to milliseconds upstream.
- Include `device_key` when available to filter per-device runs.
- Store raw payload in `raw` for debugging while keeping `metadata` concise for analysis.
- Use IAM roles and least-privilege for S3/Athena access; avoid embedding long-lived credentials in configs.

Next steps for data teams
1. Pull `examples/demo_events.jsonl` to test locally.
2. Run the notebook `examples/notebooks/s3_quickstart.ipynb` to see basic KPIs.
3. Add a short adapter or ETL to project raw logs into `NormalizedEvent` and validate with `examples/validate_demo.py`.
