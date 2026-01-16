"""Simple validator for examples/demo_events.jsonl
"""
import json
from pathlib import Path

from screen2events.models import NormalizedEvent

p = Path(__file__).parent / "demo_events.jsonl"
if not p.exists():
    raise SystemExit("demo_events.jsonl not found")

count = 0
errs = 0
for line in p.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    count += 1
    try:
        obj = json.loads(line)
        NormalizedEvent.model_validate(obj)
    except Exception as e:
        print(f"Invalid record: {e}\n{line}")
        errs += 1

print(f"Parsed {count} records, errors={errs}")
if errs:
    raise SystemExit(2)
