Application & Pipeline Tracker

Scope
-----
Validate and extend `src/pipeline.py`, ensure `src/memory_setup.py` behaves as expected, and ensure `app` container command is correct for development and production.

Subtasks
--------
- [ ] Run `src/pipeline.py` locally (inside container) and verify it can connect to `ollama` — estimate: 2h
- [ ] Add logs and error handling for network errors and missing dependencies — estimate: 2h
- [ ] Add a small integration test for pipeline run writing into `chroma_db` — estimate: 1d

Acceptance Criteria
-------------------
- Pipeline runs end-to-end and writes to `chroma_db` with sample input.
- Errors are surfaced with actionable messages.

Priority: High
