# Branch Update Quick Reference

> **TL;DR:** Run `./scripts/update-subsidiary-branches.sh` to update all branches. 4 branches will need manual conflict resolution. Full docs in BRANCH_UPDATE_STRATEGY.md

---

## ⚡ Quick Commands

```bash
# Test what would happen (safe, no changes)
./scripts/update-subsidiary-branches.sh --dry-run

# Update all branches
./scripts/update-subsidiary-branches.sh

# Manual conflict resolution
git checkout <branch-with-conflict>
git merge origin/main
# Fix conflicts in README.md and src/orchestrator.py
git add .
git commit -m "chore: merge main and resolve conflicts"
git push origin <branch-name>
```

---

## 📊 Current Status

| Branch | Status | Action |
|--------|--------|--------|
| `copilot/dev-ux-feature-branch` | ✅ Current | None needed |
| `copilot/initialize-gpu-resource-manager` | ✅ Current | None needed |
| `copilot/start-task-04-langflow` | 🟢 Ready | Auto-update |
| `feature/infra-scaffold-v2` | 🟢 Ready | Auto-update |
| `copilot/integrate-signal-emitter-consumer` | 🟡 Conflicts | Manual fix |
| `copilot/merge-feature-branches-for-task-07` | 🟡 Conflicts | Manual fix |
| `copilot/prepare-documentation-automation` | 🟡 Conflicts | Manual fix |
| `copilot/start-enclaves-zephyr-task05` | 🟡 Conflicts | Manual fix |

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| `BRANCH_UPDATE_STRATEGY.md` | Why we're doing this, what's changing |
| `CONFLICT_RESOLUTION_GUIDE.md` | Step-by-step conflict fixes |
| `BRANCH_UPDATE_EXECUTION_SUMMARY.md` | Complete execution guide |
| `scripts/update-subsidiary-branches.sh` | The automation tool |
| This file | Quick reference |

---

## 🔧 Common Conflict Resolution

### README.md Conflicts
```bash
# Strategy: Keep main's structure, add unique branch content
vim README.md
# Remove <<<<<<, =======, >>>>>> markers
# Merge sections logically
git add README.md
```

### src/orchestrator.py Conflicts
```bash
# Strategy: Use main's version (it's newer)
git checkout --theirs src/orchestrator.py
git add src/orchestrator.py
```

---

## 🎯 What's Being Merged

**From main (PR #30):**
- MCP server configs
- Observability stack (Prometheus, Grafana, Loki, Tempo)
- RAG pipeline services
- Universal deployment scripts
- Langflow examples
- SSL/DNS management
- DevContainer setup
- OpenTelemetry updates (1.28.2 → 1.34.0)

**Impact:** ~13,462 lines added across 94 files

---

## ✅ Success Criteria

- [ ] 2 clean branches updated and pushed
- [ ] 4 conflicted branches resolved and pushed
- [ ] All branches build successfully
- [ ] No CI failures introduced

---

## 🆘 Need Help?

1. **Script errors?** Check `BRANCH_UPDATE_EXECUTION_SUMMARY.md` → Troubleshooting section
2. **Conflicts?** See `CONFLICT_RESOLUTION_GUIDE.md` for step-by-step resolution
3. **Why is this needed?** Read `BRANCH_UPDATE_STRATEGY.md` for full context

---

## 🚀 Execution Steps

1. ✅ Analysis and documentation (DONE)
2. ⏭️ Run automated script for clean branches
3. ⏭️ Manually resolve 4 conflicted branches
4. ⏭️ Validate all branches build/test successfully

---

**Last Updated:** 2025-12-22  
**Script Version:** 1.0  
**Status:** Ready for execution
