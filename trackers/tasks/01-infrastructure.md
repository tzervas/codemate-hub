Infrastructure Tracker

Scope
-----
Ensure `docker-compose.yml` and `Dockerfile` run reliably on target hosts (with/without GPU).

Subtasks
--------
- [ ] Validate `docker-compose up` on a fresh host (no GPU) — estimate: 1h
- [ ] Validate `ollama` health check and fallback when no GPU — estimate: 2h
- [ ] Add clear troubleshooting notes for common Docker errors — estimate: 1h
- [ ] Add CI smoke test that runs `docker-compose` in a lightweight environment — estimate: 1-2d

Acceptance Criteria
-------------------
- `docker-compose up` brings services to healthy states on Linux hosts.
- Documented steps for GPU vs CPU activation.

Priority: High
