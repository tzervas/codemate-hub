#!/bin/bash
# Script to push all feature branches to remote
# Run this script to publish all feature branches created for remaining tasks

set -euo pipefail

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Pushing all feature branches to remote...${NC}"

branches=(
    "feature/task-04-langflow"
    "feature/task-05-enclaves-zephyr"
    "feature/task-06-dev-ux"
    "feature/task-07-automation-scripts"
    "feature/task-08-docs-qa"
)

for branch in "${branches[@]}"; do
    echo -e "${BLUE}Pushing $branch...${NC}"
    git push -u origin "$branch"
    echo -e "${GREEN}✅ Pushed $branch${NC}"
done

echo ""
echo -e "${GREEN}✅ All feature branches pushed successfully!${NC}"
echo ""
echo "Available branches:"
git branch -r | grep feature/task || echo "No feature branches found in remote (yet)"
