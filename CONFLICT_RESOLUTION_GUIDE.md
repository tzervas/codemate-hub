# Manual Conflict Resolution Guide

This document provides step-by-step instructions for resolving conflicts when updating subsidiary branches with changes from main.

## Overview

Based on the dry-run analysis, 4 branches have merge conflicts that require manual resolution:

1. `copilot/integrate-signal-emitter-consumer`
2. `copilot/merge-feature-branches-for-task-07`
3. `copilot/prepare-documentation-automation`
4. `copilot/start-enclaves-zephyr-task05`

## Common Conflict Files

The conflicts are primarily in:
- `README.md` - Documentation updates from both branches
- `src/orchestrator.py` - New file added in both main and the branch

## Resolution Strategy

### For README.md Conflicts

The README.md file likely has additions from both branches. Resolution strategy:

1. Keep the structure from main (it has the latest organization)
2. Merge in any unique content from the branch
3. Ensure all sections are cohesive and non-contradictory

**Steps:**
```bash
# 1. Open the file
vim README.md  # or your editor of choice

# 2. Look for conflict markers
<<<<<<< HEAD (branch version)
... content from branch ...
=======
... content from main ...
>>>>>>> origin/main

# 3. Merge the content manually:
# - Keep main's structure and latest sections
# - Add any unique information from the branch
# - Remove conflict markers

# 4. Save and mark as resolved
git add README.md
```

### For src/orchestrator.py Conflicts

This file was added in both branches. The versions are likely similar but might have different implementations.

**Resolution Strategy:**

1. **Compare the implementations**:
   ```bash
   # Show both versions side by side
   git show :2:src/orchestrator.py > /tmp/orchestrator_branch.py
   git show :3:src/orchestrator.py > /tmp/orchestrator_main.py
   diff -u /tmp/orchestrator_branch.py /tmp/orchestrator_main.py
   ```

2. **Decide which version to keep**:
   - If main's version is more complete → use main's version
   - If branch's version has unique features → merge both
   - If they're fundamentally different → choose one and note the other for future work

3. **Resolve**:
   ```bash
   # Option A: Keep main's version
   git checkout --theirs src/orchestrator.py
   git add src/orchestrator.py
   
   # Option B: Keep branch's version
   git checkout --ours src/orchestrator.py
   git add src/orchestrator.py
   
   # Option C: Manual merge (open in editor and combine)
   vim src/orchestrator.py
   # Merge content manually
   git add src/orchestrator.py
   ```

## Step-by-Step Resolution Process

### Branch 1: copilot/integrate-signal-emitter-consumer

```bash
# 1. Checkout the branch
git checkout copilot/integrate-signal-emitter-consumer

# 2. Attempt merge
git merge origin/main --no-edit -m "chore: merge main into copilot/integrate-signal-emitter-consumer"

# 3. If conflicts, list them
git status

# 4. For README.md:
# - Open in editor
# - Merge documentation sections
# - Prioritize main's structure with unique branch content
vim README.md
git add README.md

# 5. For src/orchestrator.py:
# - Compare versions
git show :2:src/orchestrator.py > /tmp/orch_branch.py
git show :3:src/orchestrator.py > /tmp/orch_main.py
diff -u /tmp/orch_branch.py /tmp/orch_main.py

# - Decide strategy (likely keep main's version as it's more recent)
git checkout --theirs src/orchestrator.py
git add src/orchestrator.py

# 6. Complete the merge
git commit -m "chore: merge main and resolve conflicts"

# 7. Push
git push origin copilot/integrate-signal-emitter-consumer
```

### Branch 2: copilot/merge-feature-branches-for-task-07

```bash
# 1. Checkout the branch
git checkout copilot/merge-feature-branches-for-task-07

# 2. Attempt merge
git merge origin/main --no-edit -m "chore: merge main into copilot/merge-feature-branches-for-task-07"

# 3. Resolve conflicts following same pattern as above

# 4. Key files to check:
#    - README.md (merge documentation)
#    - scripts/*.sh (keep both changes if they don't overlap)

# 5. Commit and push
git commit -m "chore: merge main and resolve conflicts"
git push origin copilot/merge-feature-branches-for-task-07
```

### Branch 3: copilot/prepare-documentation-automation

```bash
# 1. Checkout the branch
git checkout copilot/prepare-documentation-automation

# 2. Attempt merge
git merge origin/main --no-edit -m "chore: merge main into copilot/prepare-documentation-automation"

# 3. Resolve conflicts
#    This branch likely has documentation conflicts
#    Strategy: Keep main's structure, merge branch's documentation automation details

# 4. Commit and push
git commit -m "chore: merge main and resolve conflicts"
git push origin copilot/prepare-documentation-automation
```

### Branch 4: copilot/start-enclaves-zephyr-task05

```bash
# 1. Checkout the branch
git checkout copilot/start-enclaves-zephyr-task05

# 2. Attempt merge
git merge origin/main --no-edit -m "chore: merge main into copilot/start-enclaves-zephyr-task05"

# 3. Resolve conflicts
#    Focus on zephyr/ directory and README.md

# 4. Commit and push
git commit -m "chore: merge main and resolve conflicts"
git push origin copilot/start-enclaves-zephyr-task05
```

## General Conflict Resolution Tips

### 1. Understanding Conflict Markers

```
<<<<<<< HEAD (current branch)
Content from your branch
=======
Content from main
>>>>>>> origin/main
```

### 2. Resolution Commands

```bash
# Accept theirs (main's version)
git checkout --theirs <file>

# Accept ours (branch's version)
git checkout --ours <file>

# View both versions
git show :2:<file>  # Branch version
git show :3:<file>  # Main version
```

### 3. Verification

After resolving conflicts:
```bash
# Check that all conflicts are resolved
git status

# Review the changes
git diff --cached

# Run any tests
./scripts/test-integration.sh

# Build to ensure nothing is broken
./scripts/build.sh
```

### 4. If Resolution is Too Complex

If conflicts are too complex to resolve:

1. **Abort the merge**:
   ```bash
   git merge --abort
   ```

2. **Document the issue**:
   ```bash
   echo "Branch <name> has complex conflicts in <files>" >> /tmp/conflicts.txt
   ```

3. **Consider alternative strategies**:
   - Rebase instead of merge
   - Create a new branch from main and cherry-pick changes
   - Manually port changes to a fresh branch

## Post-Resolution Checklist

After resolving conflicts for each branch:

- [ ] All conflict markers removed
- [ ] Code compiles/builds successfully
- [ ] Tests pass (if applicable)
- [ ] Changes committed with clear message
- [ ] Branch pushed to origin
- [ ] Updated BRANCH_UPDATE_STRATEGY.md status

## Automated Resolution Helper

For quick resolution of simple conflicts:

```bash
#!/bin/bash
# Helper script for automated conflict resolution

resolve_readme_conflict() {
    # For README.md, typically want to keep main's structure
    # with additional sections from branch
    
    if git diff --name-only --diff-filter=U | grep -q README.md; then
        echo "README.md has conflicts - manual review required"
        # Could add automated resolution logic here
    fi
}

resolve_orchestrator_conflict() {
    # For src/orchestrator.py, typically want main's version
    
    if git diff --name-only --diff-filter=U | grep -q src/orchestrator.py; then
        echo "Using main's version of orchestrator.py"
        git checkout --theirs src/orchestrator.py
        git add src/orchestrator.py
    fi
}

# Run helpers
resolve_readme_conflict
resolve_orchestrator_conflict
```

## Summary

The automated script successfully updated 2 branches without conflicts:
- ✅ copilot/start-task-04-langflow
- ✅ feature/infra-scaffold-v2

The following 4 branches need manual conflict resolution:
- ❌ copilot/integrate-signal-emitter-consumer
- ❌ copilot/merge-feature-branches-for-task-07
- ❌ copilot/prepare-documentation-automation
- ❌ copilot/start-enclaves-zephyr-task05

The following 2 branches were already up-to-date:
- ✅ copilot/dev-ux-feature-branch (already merged main)
- ✅ copilot/initialize-gpu-resource-manager (already up-to-date)
