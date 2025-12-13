Automation & Scripts Tracker

Scope
-----
Ensure `scripts/` automate build, deploy, model pulls, and teardown reliably.

Subtasks
--------
- [ ] Review `scripts/build.sh`, `deploy.sh`, `model-pull.sh`, `teardown.sh` for idempotency — estimate: 1h
- [ ] Add safety checks for missing env vars (e.g., `PASSWORD`) — estimate: 30m
- [ ] Add a `scripts/check-health.sh` that waits for service healthchecks — estimate: 1h

Acceptance Criteria
-------------------
- Scripts run idempotently and fail early with clear messages.

Priority: Medium
