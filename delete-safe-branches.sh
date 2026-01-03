#!/bin/bash
#
# Branch Deletion Script - Safe to Delete Branches
# Deletes 93 archived branches (excludes copilot and sentinel)
#
# PREREQUISITES:
# 1. Archive tags must be pushed to remote: git push origin --tags
# 2. Verification that tags exist remotely
# 3. Approval from stakeholders
#

set -e

REPO_DIR="/home/runner/work/a-i-council--coliseum/a-i-council--coliseum"
cd "$REPO_DIR"

# Dry run flag
DRY_RUN="${1:-true}"

if [ "$DRY_RUN" = "true" ]; then
    echo "=== DRY RUN MODE - No branches will be deleted ==="
    echo "Run with: $0 false  (to execute deletions)"
    echo ""
fi

echo "=== Branch Deletion: Safe-to-Delete Branches ==="
echo ""

# Get all branches that are safe to delete
# Excludes: copilot/* and sentinel*
SAFE_BRANCHES=$(git ls-remote --heads origin | \
    awk '{print $2}' | \
    sed 's|refs/heads/||' | \
    grep -v '^main$' | \
    grep -v '^copilot/' | \
    grep -v '^sentinel' | \
    sort || true)

TOTAL=$(echo "$SAFE_BRANCHES" | grep -v '^$' | wc -l)
DELETED=0

echo "Found $TOTAL branches safe to delete:"
echo ""
echo "Categories included:"
echo "- BOLT performance branches (~22)"
echo "- PALETTE UI branches (~22)"
echo "- Feature development branches (~39)"
echo "- Other branches (~10)"
echo ""
echo "Categories EXCLUDED (protected):"
echo "- copilot/* branches (active work)"
echo "- sentinel* branches (require security review)"
echo ""

# Verify archive tags exist
echo "Verifying archive tags exist locally..."
MISSING_TAGS=0
while IFS= read -r BRANCH; do
    if [ -z "$BRANCH" ]; then
        continue
    fi
    
    TAG_NAME="archive/$BRANCH"
    if ! git rev-parse "$TAG_NAME" >/dev/null 2>&1; then
        echo "⚠ WARNING: Missing archive tag for: $BRANCH"
        MISSING_TAGS=$((MISSING_TAGS + 1))
    fi
done <<< "$SAFE_BRANCHES"

if [ $MISSING_TAGS -gt 0 ]; then
    echo ""
    echo "ERROR: $MISSING_TAGS branches are missing archive tags!"
    echo "Cannot proceed with deletion. Create missing tags first."
    exit 1
fi

echo "✓ All $TOTAL branches have archive tags"
echo ""

if [ "$DRY_RUN" = "true" ]; then
    echo "Would delete the following branches:"
    echo "$SAFE_BRANCHES" | head -20
    if [ $TOTAL -gt 20 ]; then
        echo "... and $((TOTAL - 20)) more"
    fi
    echo ""
    echo "To execute deletion, run: $0 false"
    exit 0
fi

# Actual deletion
echo "Starting deletion of $TOTAL branches..."
echo ""

while IFS= read -r BRANCH; do
    if [ -z "$BRANCH" ]; then
        continue
    fi
    
    echo "Deleting: $BRANCH"
    if git push origin --delete "$BRANCH" 2>/dev/null; then
        DELETED=$((DELETED + 1))
        if [ $((DELETED % 10)) -eq 0 ]; then
            echo "Progress: $DELETED/$TOTAL deleted..."
        fi
    else
        echo "⚠ Failed to delete: $BRANCH"
    fi
done <<< "$SAFE_BRANCHES"

echo ""
echo "=== Deletion Complete ==="
echo "Deleted: $DELETED/$TOTAL branches"
echo ""
echo "Protected branches remaining:"
echo "- 6 copilot/* branches"
echo "- 20 sentinel* branches"
echo "- 1 main branch"
echo "- 1 copilot/deep-clean-open-prs (current PR)"
echo ""
echo "Total remaining: ~28 branches"
