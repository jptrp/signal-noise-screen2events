# AI Coding Agent Instructions for Signal & Noise (screen2events)

## Project Overview
**Screen-to-Events** is a reference implementation for hardware-in-the-loop observability that correlates **what users see** on a TV/device screen with **what telemetry claims happened**. The screen is treated as ground truth; telemetry is a set of claims to be validated.

## Architecture & Data Flow

### Core Pipeline
```
Video Frame → Vision Analysis → State Timeline (Observations)
IR Actions → Control Verification
Telemetry Stream → Event Adapters → Normalized Events
Observations + Events + Alignment → Correlation → Evidence Report
```

### Key Components

**`video/`** — Vision and state extraction
- `state_machine.py`: MVP explainable state machine (uses motion detection, optional OCR)
- `detectors.py`: Classifies frame signals into UX states (PLAYBACK, BUFFERING, AD, ERROR, etc.)
- `capture.py`, `motion.py`, `ocr.py`: Low-level frame processing

**`events/`** — Vendor-agnostic telemetry adapters
- `adapter_base.py`: Abstract `EventAdapter` interface; all telemetry sources conform to this
- `file_adapter.py`: Public demo (reads normalized events from JSONL)
- `athena_adapter.py`, `opensearch_adapter.py`: Skeleton adapters for cloud sources
- `normalize.py`: Converts vendor schemas to `NormalizedEvent`

**`correlate/`** — Timeline alignment & matching
- `align.py`: Estimates clock offset/drift between video time and event time using anchor points
- `match.py`: Coarse event↔observation matching based on event kind → UX state mappings
- `anomalies.py`: Generates findings (warnings/errors) for mismatches

**`control/`** — IR automation & verification
- `ir.py`: IR blaster abstractions
- `verify.py`: Visual verification that remote commands actually changed state

**`session_id/`** — Device/session identity resolution
- `resolve.py`: Bootstrap mode (learn device identity) vs. known-device mode (filter telemetry deterministically)

**`report/`** — Output generation
- `render_md.py`: Markdown report with timelines and mismatches
- `evidence.py`: Exports evidence frames from video for problematic observations

## Critical Patterns & Conventions

### 1. **Pydantic Models are the Contract**
All data structures use Pydantic v2. Key models in [models.py](src/screen2events/models.py):
- `Observation`: Screen-derived state at video timestamp (t_video_ms, state, confidence, signals)
- `NormalizedEvent`: Vendor-agnostic telemetry event (t_event_ms, kind, session_key, device_key, metadata)
- `Alignment`: Time offset + drift between video and event clocks
- `Finding`: Mismatch evidence with severity (INFO/WARN/ERROR)

**Don't invent new fields; extend metadata dicts** (`signals` in Observation, `metadata`/`raw` in NormalizedEvent).

### 2. **Adapter Pattern for Extensibility**
Telemetry sources are pluggable. New adapters must:
1. Inherit `EventAdapter` from [events/adapter_base.py](src/screen2events/events/adapter_base.py)
2. Implement `fetch(q: EventQuery) → Iterable[NormalizedEvent]`
3. Normalize vendor schemas (timestamps in ms, extract session_key/device_key if available)
4. Store raw payloads in `raw` field for debugging

Example: [events/file_adapter.py](src/screen2events/events/file_adapter.py) is the public demo.

### 3. **Screen is Ground Truth**
Design decision: Vision observations gate telemetry queries.
- `cli.py` detects `APP_OPEN` state (or uses explicit `app_open_video_ms` from config)
- Telemetry queries start after gate point (no backfill before app opens)
- See [cli.py](src/screen2events/cli.py) `_detect_app_open()` function

### 4. **State Machine is Intentionally Simple**
[video/state_machine.py](src/screen2events/video/state_machine.py) uses:
- **Motion detection** for activity (not just video stability)
- **Optional OCR** for text-based clues (e.g., "Loading", "Error" overlays)
- **No ML/opaque magic** for MVP reliability; heuristics over neural nets

Extend by adding new detectors in [detectors.py](src/screen2events/video/detectors.py), not the state machine itself.

### 5. **Time Alignment is Bidirectional**
Observations use `t_video_ms` (video timeline). Events use `t_event_ms` (event timeline).
- `Alignment.offset_ms`: add to video_ms to estimate event_ms
- Formula: `event_ms ≈ video_ms + offset_ms + (video_ms * drift_ppm / 1_000_000)`
- Alignment is computed once using anchor points (e.g., session_start event ↔ app_open state)
- See [correlate/align.py](src/screen2events/correlate/align.py)

### 6. **Finding Severity Levels**
Findings reflect the type of mismatch:
- **INFO**: Expected behaviors (e.g., late telemetry)
- **WARN**: Discrepancies that might indicate issues
- **ERROR**: Critical mismatches (e.g., event claims state never seen on screen)

See [correlate/anomalies.py](src/screen2events/correlate/anomalies.py) for examples.

## Development Workflow

### Run a Full Session
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[video,dev]"  # video: opencv + tesseract; dev: pytest + ruff + mypy
pytest
s2e run --config examples/config.example.yaml --video /path/to/video.mp4 --out runs
```

### Key Commands
- `s2e run`: Main pipeline (see [cli.py](src/screen2events/cli.py))
- `pytest`: Unit tests in [tests/](tests/)
- `ruff check src/`: Linter (100-char line limit, enforced in pyproject.toml)
- `mypy src/`: Type checking

### Config File (YAML)
See [examples/config.example.yaml](examples/config.example.yaml). Options:
- `run_id`: Label for this run
- `app_open_video_ms`: Explicit gate point (auto-detected if omitted)
- `device_key`: Filter telemetry by device (optional)
- `video.sample_fps`: Frame sampling rate (default 10)
- `video.enable_ocr`: Use Tesseract OCR (slow, optional)
- `telemetry.adapter`: "file" (demo) or "athena"/"opensearch" (cloud)
- `telemetry.events_file`: Path to JSONL of normalized events

### Output Structure
Each run creates a timestamped directory under `runs/`:
```
runs/20250115_143022/
  observations.jsonl        # Screen-derived states
  gate.json                 # APP_OPEN timestamp
  events.jsonl              # Normalized telemetry
  alignment.json            # Clock offset/drift
  matches.jsonl             # Event↔observation pairs
  findings.jsonl            # Mismatches + evidence
  report.md                 # Human-readable summary
  evidence/                 # Screenshot frames for findings
```

## Testing & Validation

### Unit Tests
- `tests/test_match.py`: Event↔observation matching logic
- Run with `pytest` (pythonpath set in [pytest.ini](pytest.ini))
- Models have validation; test edge cases (e.g., empty observations, misaligned timelines)

### Manual Testing
- Record video or use examples if available
- Normalize a sample telemetry JSON/JSONL to the `NormalizedEvent` schema
- Run pipeline end-to-end; examine report and findings

## Common Modifications

### Adding a New UX State
1. Add to `UXState` enum in [models.py](src/screen2events/models.py)
2. Update `classify_state()` in [video/detectors.py](src/screen2events/video/detectors.py)
3. Update `kind_to_state` mapping in [correlate/match.py](src/screen2events/correlate/match.py#MatchConfig) if applicable
4. Add test coverage in [tests/test_match.py](tests/test_match.py)

### Adding a Cloud Telemetry Source
1. Create new adapter in `events/` (e.g., `custom_adapter.py`)
2. Inherit `EventAdapter`, implement `fetch(q: EventQuery)`
3. Normalize timestamps to milliseconds; populate `session_key`, `device_key`, `kind`
4. Update `load_config()` to recognize your adapter type
5. Add optional dependency group in [pyproject.toml](pyproject.toml) if needed

### Tweaking Vision Detectors
- Update motion thresholds in [video/motion.py](src/screen2events/video/motion.py)
- Add OCR-based rules to `classify_state()` in [video/detectors.py](src/screen2events/video/detectors.py)
- Test with `--max-frames 100` for quick iteration

## Design Principles (Reference)
- **Screen first**: Treat video as source of truth.
- **Verify actions**: Remote commands are not trusted until visually confirmed.
- **Gate telemetry**: Do not correlate telemetry until target app is visible.
- **Be generic**: No assumptions about proprietary schemas.
- **Prefer explainable heuristics**: Simple state machines over opaque magic.

## Dependencies & Requirements
- **Python**: ≥3.10
- **Core**: pydantic ≥2.6, pyyaml ≥6.0, typer ≥0.12, rich ≥13.7
- **Video**: opencv-python ≥4.9, pytesseract ≥0.3.10 (optional; requires system tesseract)
- **Cloud**: boto3, pyathena, opensearch-py (optional; for cloud adapters)
- **Dev**: pytest ≥8.0, ruff ≥0.5, mypy ≥1.8

See [pyproject.toml](pyproject.toml) for exact versions.
