Langflow Tracker

Scope
-----
Create stable Langflow flows, ensure `langflow_data` is persisted, and document how to export/import flows.

Subtasks
--------
- [ ] Inspect `langflow` container config and confirm DB path `./langflow_data/langflow.db` — estimate: 15m
- [ ] Create example flows and export them into `langflow_data` — estimate: 2-4h
- [ ] Document flow patterns and mapping to `src/pipeline.py` — estimate: 2h

Acceptance Criteria
-------------------
- Example flows exist in `langflow_data` and reproduceable via import.

Priority: Medium
