#!/bin/bash
# Script to update all subsidiary branches with latest changes from main
# 
# This script merges the latest changes from main into all feature and copilot branches
# that are based on main but haven't been updated with recent merges.
#
# Usage: ./scripts/update-subsidiary-branches.sh [--dry-run]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo -e "${YELLOW}Running in DRY-RUN mode - no changes will be pushed${NC}"
fi

echo -e "${BLUE}=== Branch Update Script ===${NC}"
echo "This script will update subsidiary branches with changes from main"
echo ""

# Ensure we're on the latest main
echo "Fetching latest changes from origin..."
git fetch origin

# List of branches to update
BRANCHES_TO_UPDATE=(
    "copilot/dev-ux-feature-branch"
    "copilot/initialize-gpu-resource-manager"
    "copilot/integrate-signal-emitter-consumer"
    "copilot/merge-feature-branches-for-task-07"
    "copilot/prepare-documentation-automation"
    "copilot/start-enclaves-zephyr-task05"
    "copilot/start-task-04-langflow"
    "feature/infra-scaffold-v2"
)

# Track results
UPDATED=()
CONFLICTS=()
SKIPPED=()
CURRENT_BRANCH=$(git branch --show-current)

for branch in "${BRANCHES_TO_UPDATE[@]}"; do
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Processing: $branch${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Check if branch exists remotely
    if ! git ls-remote --heads origin | grep -q "refs/heads/$branch"; then
        echo -e "${YELLOW}⚠ Branch $branch does not exist remotely, skipping${NC}"
        SKIPPED+=("$branch (not found)")
        continue
    fi
    
    # Fetch the branch from remote
    echo "Fetching $branch from origin..."
    git fetch origin "$branch:$branch" 2>/dev/null || true
    
    # Checkout the branch
    echo "Checking out $branch..."
    if ! git checkout "$branch" 2>/dev/null; then
        echo -e "${YELLOW}⚠ Failed to checkout $branch, skipping${NC}"
        SKIPPED+=("$branch (checkout failed)")
        continue
    fi
    
    # Pull latest changes
    echo "Pulling latest changes for $branch..."
    git pull origin "$branch" --ff-only 2>/dev/null || git pull origin "$branch" 2>/dev/null || true
    
    # Check how many commits behind main
    COMMITS_BEHIND=$(git log --oneline HEAD..origin/main | wc -l)
    echo "Branch is $COMMITS_BEHIND commits behind main"
    
    # Check if branch already has the latest main commits
    if git merge-base --is-ancestor origin/main HEAD 2>/dev/null; then
        echo -e "${GREEN}✓ Branch $branch already has all commits from main${NC}"
        SKIPPED+=("$branch (up-to-date)")
        continue
    fi
    
    # Show what commits will be merged
    echo -e "\n${BLUE}Commits from main that will be merged:${NC}"
    git log --oneline --graph HEAD..origin/main | head -10
    echo ""
    
    # Try to merge main
    echo "Merging main into $branch..."
    if git merge origin/main --no-edit -m "chore: merge main into $branch"; then
        echo -e "${GREEN}✓ Successfully merged main${NC}"
        
        # Show merge statistics
        echo -e "\n${BLUE}Merge statistics:${NC}"
        git diff --stat HEAD~1 HEAD
        
        if [ "$DRY_RUN" = true ]; then
            echo -e "${YELLOW}DRY-RUN: Would push updated $branch${NC}"
            # Reset the merge in dry-run mode
            git reset --hard HEAD~1
            UPDATED+=("$branch (dry-run)")
        else
            # Push the updated branch
            echo "Pushing updated $branch..."
            if git push origin "$branch"; then
                echo -e "${GREEN}✓ Successfully pushed $branch${NC}"
                UPDATED+=("$branch")
            else
                echo -e "${RED}✗ Failed to push $branch${NC}"
                # Reset the merge if push failed
                git reset --hard HEAD~1
            fi
        fi
    else
        echo -e "${RED}✗ Conflict detected when merging main${NC}"
        echo -e "${YELLOW}Aborting merge...${NC}"
        git merge --abort
        CONFLICTS+=("$branch")
        continue
    fi
done

# Return to the original branch
echo -e "\n${BLUE}Returning to original branch: $CURRENT_BRANCH${NC}"
git checkout "$CURRENT_BRANCH"

# Summary
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}=== Update Summary ===${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${GREEN}Successfully updated (${#UPDATED[@]}):${NC}"
if [ ${#UPDATED[@]} -eq 0 ]; then
    echo "  (none)"
else
    for branch in "${UPDATED[@]}"; do
        echo "  ✓ $branch"
    done
fi

echo -e "\n${RED}Conflicts detected (${#CONFLICTS[@]}):${NC}"
if [ ${#CONFLICTS[@]} -eq 0 ]; then
    echo "  (none)"
else
    for branch in "${CONFLICTS[@]}"; do
        echo "  ✗ $branch"
    done
fi

echo -e "\n${YELLOW}Skipped (${#SKIPPED[@]}):${NC}"
if [ ${#SKIPPED[@]} -eq 0 ]; then
    echo "  (none)"
else
    for branch in "${SKIPPED[@]}"; do
        echo "  - $branch"
    done
fi

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}DRY-RUN complete. No changes were pushed.${NC}"
    echo -e "${YELLOW}Run without --dry-run to actually update branches.${NC}"
else
    echo -e "${GREEN}Update process complete!${NC}"
fi

# Exit with error if there were conflicts
if [ ${#CONFLICTS[@]} -gt 0 ]; then
    echo -e "\n${RED}⚠ Some branches had conflicts and were not updated.${NC}"
    echo -e "${RED}Please review and resolve conflicts manually.${NC}"
    exit 1
fi
