# Task 03: Application & Pipeline Planning Notes

_Last updated: 2025-12-13_

## Purpose
- Capture the granular planning discussion for Task 03 (Application & Pipeline).
- Preserve decisions around fixture-based regression coverage and pipeline orchestration.

## Summary of Decisions
- Pipeline validation will operate **exclusively in fixture mode**; no live Ollama inference during tests.
- Use a deterministic matrix of responses (success, HTTP error, malformed schema) to exercise behavior.
- Emulate persistence through temporary or in-memory storage to avoid touching real Chroma volumes.
- `PipelineResult` objects and structured logging must capture outcomes for both success and failure paths.
- Regression harness must be fast enough for GitHub Actions test containers.

## Test Matrix Expectations
- Success fixture: HTTP 200, well-formed body, embeddings persisted, result returned.
- HTTP error fixture: non-200 response, `PipelineError` raised, memory untouched, failure logged.
- Malformed schema fixture: missing/invalid fields, validation failure raised, memory untouched, failure logged.

## Implementation Notes
- Introduce an injectable client abstraction so tests can load JSON fixtures; default execution remains fixture-driven.
- Use temporary directories (or mock persistence layer) inside tests to simulate `chroma_db` writes.
- Ensure clean-up and guardrails prevent partial writes when errors occur.
- Add concise JSON fixtures under `tests/fixtures/` for each matrix scenario.
- Extend CI workflow with a quick `uv run pytest` job to run the regression suite.

## Next Steps
1. Create fixture assets and document schema snippets in `README.md`.
2. Implement the pipeline orchestration (`run_pipeline`) using fixture-backed client and structured result/exception types.
3. Add regression tests for all matrix entries and integrate them into CI.
4. Update trackers, documentation, and changelog once implementation and tests land.
