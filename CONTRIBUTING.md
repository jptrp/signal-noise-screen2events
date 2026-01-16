# Contributing

Thanks for contributing! This project uses an adapter pattern for telemetry sources and a small, explainable vision pipeline.

How to add an adapter
1. Create a new file under `src/screen2events/events/` inheriting `EventAdapter` (see `adapter_base.py`).
2. Implement `fetch(q: EventQuery) -> Iterable[NormalizedEvent]` and normalize timestamps to milliseconds.
3. Add optional extras to `pyproject.toml` if your adapter needs external libs (e.g., `boto3`, `pyathena`, `opensearch-py`).
4. Add an example config under `examples/` and update `README.md` to reference it.

Testing
- Add unit tests under `tests/` and ensure `pytest` passes locally.
- Include a small `examples/demo_events.jsonl` for sample-driven tests.

Security
- Do not commit long-lived credentials. Use environment variables, IAM roles, or `aws` profiles.

PR checklist
- [ ] Tests added/updated
- [ ] Docs updated (README or examples)
- [ ] Demo data included when relevant
- [ ] Optional extras added to `pyproject.toml` if new deps are required

Contact
- Open an issue or PR on the repo. Include sample events and a short description of the integration.
