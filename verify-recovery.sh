#!/bin/bash
# Branch Recovery Verification Script
# Run this AFTER the other developer pushes the branches

echo "═══════════════════════════════════════════════════════════"
echo "Branch Recovery Verification"
echo "═══════════════════════════════════════════════════════════"
echo ""

echo "📥 Fetching latest from GitHub..."
git fetch origin --prune
echo ""

echo "📋 Checking for recovered branches..."
echo ""

EXPECTED_BRANCHES=(
    "E2-Update"
    "Epic1-S11"
    "Epic2"
    "Epic2-07"
    "Epic3-07"
    "Epic4"
    "Epic5"
    "Epic6"
    "Epic7"
    "Epic8"
    "NewEpics"
    "feature/epic8-complete-with-testing"
    "claude/validate-workflow-extraction-aV5Yo"
    "romantic-leavitt"
)

RECOVERED=0
MISSING=0

for branch in "${EXPECTED_BRANCHES[@]}"; do
    if git ls-remote --heads origin "$branch" | grep -q "$branch"; then
        echo "  ✅ $branch - RECOVERED"
        ((RECOVERED++))
    else
        echo "  ❌ $branch - STILL MISSING"
        ((MISSING++))
    fi
done

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Recovery Summary:"
echo "  Recovered: $RECOVERED branches"
echo "  Missing: $MISSING branches"
echo "═══════════════════════════════════════════════════════════"
echo ""

if [ $MISSING -eq 0 ]; then
    echo "✅ All branches successfully recovered!"
    echo ""
    echo "Next steps:"
    echo "1. You can now pull/checkout any recovered branch"
    echo "2. Example: git checkout Epic1-S11"
    echo "3. Apply author cleanup to these branches if needed"
else
    echo "⚠️  Some branches are still missing."
    echo "Ask the other developer to verify they pushed all branches."
fi
