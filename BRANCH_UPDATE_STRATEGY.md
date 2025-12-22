# Branch Update Strategy

## Overview

This document describes the strategy for updating subsidiary branches with the latest changes from `main` and `devel`.

## Current Branch State (as of 2025-12-22)

### Main Branches
- **main** (660c922): Latest production branch
  - Contains PR #30 (Multimodal AI configurations, MCP servers, RAG pipelines)
  - Contains PR #20 (Comprehensive branch review and merge analysis)
  
- **devel** (233e169): Development branch with dependency fixes
  - Contains OpenTelemetry version updates
  - Note: These changes are ALREADY incorporated in main via PR #30

### Subsidiary Branches Requiring Updates

All of the following branches are based on commit 18b8c61 and are **2 commits behind main**:

1. `copilot/dev-ux-feature-branch` - Developer UX improvements
2. `copilot/initialize-gpu-resource-manager` - GPU resource management
3. `copilot/integrate-signal-emitter-consumer` - Signal-based orchestration
4. `copilot/merge-feature-branches-for-task-07` - Automation enhancements
5. `copilot/prepare-documentation-automation` - Documentation automation
6. `copilot/start-enclaves-zephyr-task05` - Zephyr enclave system
7. `copilot/start-task-04-langflow` - Langflow integration
8. `feature/infra-scaffold-v2` - Infrastructure enhancements

## Update Strategy

### Why Only Merge Main?

The `devel` branch contains dependency updates that are ALREADY in `main`. Specifically:
- OpenTelemetry API: 1.28.2 → 1.34.0
- OpenTelemetry SDK: 1.28.2 → 1.34.0
- OpenTelemetry Instrumentation: 0.49b2 → 0.53b0

Since these changes are in `main`, we only need to merge `main` into the subsidiary branches.

### Merge Order

The branches will be updated in the following order (by priority):

1. **High Priority** (Foundation for other work):
   - `copilot/integrate-signal-emitter-consumer`
   - `copilot/initialize-gpu-resource-manager`

2. **Medium Priority** (Task completion):
   - `copilot/merge-feature-branches-for-task-07`
   - `copilot/prepare-documentation-automation`
   - `copilot/start-task-04-langflow`
   - `copilot/start-enclaves-zephyr-task05`

3. **Standard Priority**:
   - `copilot/dev-ux-feature-branch`
   - `feature/infra-scaffold-v2`

## How to Update Branches

### Automated Update

Use the provided script to update all branches at once:

```bash
# Dry-run to see what would be updated
./scripts/update-subsidiary-branches.sh --dry-run

# Actually update the branches
./scripts/update-subsidiary-branches.sh
```

### Manual Update (per branch)

If you prefer to update branches manually or need to resolve conflicts:

```bash
# 1. Fetch latest changes
git fetch origin

# 2. Checkout the branch
git checkout copilot/dev-ux-feature-branch

# 3. Merge main
git merge origin/main --no-edit -m "chore: merge main into copilot/dev-ux-feature-branch"

# 4. Resolve conflicts if any (see Conflict Resolution below)

# 5. Push the updated branch
git push origin copilot/dev-ux-feature-branch

# 6. Repeat for other branches
```

## Conflict Resolution

### Expected Conflicts

Based on the branch analysis, minimal conflicts are expected because:
1. Most branches work on different areas of the codebase
2. Main's changes are primarily additions (new files/features)
3. No overlapping modifications in core files

### If Conflicts Occur

1. **Identify the conflicting files**:
   ```bash
   git status
   ```

2. **Review the conflicts**:
   ```bash
   git diff
   ```

3. **Resolve conflicts** by editing the files and choosing:
   - Keep changes from main (incoming)
   - Keep changes from branch (current)
   - Merge both changes appropriately

4. **Mark as resolved and continue**:
   ```bash
   git add <conflicted-files>
   git commit -m "chore: merge main and resolve conflicts"
   git push origin <branch-name>
   ```

### Common Conflict Scenarios

#### pyproject.toml Dependencies
- **Solution**: Keep the versions from main (they're newer and tested)

#### docker-compose.yml Services
- **Solution**: Merge both changes, ensuring no duplicate service definitions

#### Documentation Files
- **Solution**: Merge content, keeping the most comprehensive information

## Changes Being Merged

When you merge `main` into the subsidiary branches, you'll get:

### From PR #30 (Multimodal AI configurations)
- New MCP server configurations (`config/mcp/`)
- Observability stack setup (`config/observability/`, `docker-compose.observability.yml`)
- RAG pipeline services (`src/services/`, `src/tools/`)
- Enhanced deployment scripts (`scripts/deploy-universal.sh`, PowerShell scripts)
- Langflow flow examples (`config/langflow/flows/`)
- SSL/DNS management (`config/ssl/`)
- DevContainer setup (`devcontainer-ubuntu-wsl2/`)
- Comprehensive documentation (`docs/`)

### From PR #20 (Branch review)
- Branch review documentation (`BRANCH_REVIEW.md`)
- Repository state analysis (`REPOSITORY_STATE.md`)
- Quick summary (`QUICK_SUMMARY.txt`)

### From devel (Already in main)
- OpenTelemetry dependency updates (already in PR #30)

## Post-Update Validation

After updating branches, validate that:

1. **Branch compiles/builds successfully**:
   ```bash
   git checkout <branch-name>
   ./scripts/build.sh
   ```

2. **No unintended changes**:
   ```bash
   git log --oneline -5
   git diff HEAD~2 HEAD
   ```

3. **Docker services start**:
   ```bash
   ./scripts/deploy.sh
   ./scripts/check-health.sh 120
   ```

## Timeline

- **Phase 1** (Immediate): Update all 8 subsidiary branches
- **Phase 2** (Next): Update devel branch to match main
- **Phase 3** (Future): Establish continuous update process

## Notes

- The script uses `--no-edit` for merge commits to keep history clean
- All merges are non-fast-forward to preserve branch history
- Original branch authorship and commits are preserved
- Merge commits clearly indicate they're bringing in changes from main

## Troubleshooting

### Authentication Issues
If you get authentication errors when pushing:
- Ensure your GitHub credentials are properly configured
- Use SSH keys or Personal Access Tokens (PATs) with `repo` scope
- Check that you have write access to the repository

### Detached HEAD State
If you end up in a detached HEAD state:
```bash
git checkout <branch-name>
git reset --hard origin/<branch-name>
```

### Undoing an Update
If an update causes issues:
```bash
git checkout <branch-name>
git reset --hard HEAD~1  # Undo the merge commit
git push --force-with-lease origin <branch-name>
```

## Future Improvements

1. **Automated CI Check**: Add GitHub Actions workflow to notify when branches fall behind
2. **Rebase Option**: Consider rebasing strategy for cleaner history (requires force-push)
3. **Branch Protection**: Add branch protection rules to require updates before merging
4. **Update Frequency**: Establish regular schedule for updating long-lived branches
