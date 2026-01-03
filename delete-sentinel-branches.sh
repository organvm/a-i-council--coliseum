#!/bin/bash
#
# Branch Deletion Script - Sentinel (Security) Branches
# Deletes 20 sentinel branches after security review
#
# PREREQUISITES:
# 1. Archive tags must be pushed to remote: git push origin --tags
# 2. Security team review completed
# 3. Approval from security lead
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

echo "=== Branch Deletion: Sentinel (Security) Branches ==="
echo ""
echo "⚠️  WARNING: These branches may contain security fixes"
echo "⚠️  Ensure security team review is complete before deletion"
echo ""

# Get all sentinel branches
SENTINEL_BRANCHES=$(git ls-remote --heads origin | \
    awk '{print $2}' | \
    sed 's|refs/heads/||' | \
    grep '^sentinel' | \
    sort || true)

TOTAL=$(echo "$SENTINEL_BRANCHES" | grep -v '^$' | wc -l)

echo "Found $TOTAL sentinel branches:"
echo "$SENTINEL_BRANCHES"
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
done <<< "$SENTINEL_BRANCHES"

if [ $MISSING_TAGS -gt 0 ]; then
    echo ""
    echo "ERROR: $MISSING_TAGS branches are missing archive tags!"
    echo "Cannot proceed with deletion. Create missing tags first."
    exit 1
fi

echo "✓ All $TOTAL branches have archive tags"
echo ""

if [ "$DRY_RUN" = "true" ]; then
    echo "Would delete $TOTAL sentinel branches"
    echo ""
    echo "SECURITY REVIEW REQUIRED before execution"
    echo "To execute deletion after review, run: $0 false"
    exit 0
fi

# Actual deletion
echo "Starting deletion of $TOTAL sentinel branches..."
echo ""

DELETED=0
while IFS= read -r BRANCH; do
    if [ -z "$BRANCH" ]; then
        continue
    fi
    
    echo "Deleting: $BRANCH"
    if git push origin --delete "$BRANCH" 2>/dev/null; then
        DELETED=$((DELETED + 1))
    else
        echo "⚠ Failed to delete: $BRANCH"
    fi
done <<< "$SENTINEL_BRANCHES"

echo ""
echo "=== Deletion Complete ==="
echo "Deleted: $DELETED/$TOTAL sentinel branches"
