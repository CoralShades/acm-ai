#!/bin/bash
# ACM-AI RunPod Pod Cleanup
# Frees disk space by removing caches and stale test artifacts.
# Usage: bash /workspace/acm-ai/scripts/runpod/cleanup-pod.sh [--dry-run]
set -uo pipefail

REPO_DIR="/workspace/acm-ai"
DRY_RUN=false
FREED=0

[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================"
echo "  ACM-AI Pod Disk Cleanup"
echo "========================================"
$DRY_RUN && echo -e "  ${YELLOW}DRY RUN — nothing will be deleted${NC}"
echo ""

show_before() {
    echo "--- Before ---"
    df -h /workspace | tail -1 | awk '{printf "  Usage: %s (%s free)\n", $5, $4}'
    echo ""
}

clean() {
    local desc="$1" path="$2"
    if [[ -e "$path" ]]; then
        local size
        size=$(du -sh "$path" 2>/dev/null | cut -f1)
        if $DRY_RUN; then
            echo -e "  ${YELLOW}[DRY]${NC} $desc ($size): $path"
        else
            rm -rf "$path"
            echo -e "  ${GREEN}[DEL]${NC} $desc ($size): $path"
        fi
    fi
}

show_before

echo "--- Caches ---"
clean "UV cache" "/root/.cache/uv"
clean "pip cache" "/root/.cache/pip"

echo ""
echo "--- Test Artifacts ---"
# Stale test files in repo root
for f in "$REPO_DIR"/acm-page-test*.mjs; do
    [[ -e "$f" ]] && clean "Test script" "$f"
done
for f in "$REPO_DIR"/test-grid-*.png "$REPO_DIR"/old-extraction-*.png; do
    [[ -e "$f" ]] && clean "Test screenshot" "$f"
done
clean "pytest output" "$REPO_DIR/pytest_out.txt"
clean "Test results dir" "$REPO_DIR/test-results"
# Stale PDFs in repo root (not in data dir)
for f in "$REPO_DIR"/*.pdf; do
    [[ -e "$f" ]] && clean "Stale PDF in repo root" "$f"
done

echo ""
echo "--- After ---"
df -h /workspace | tail -1 | awk '{printf "  Usage: %s (%s free)\n", $5, $4}'
echo ""
$DRY_RUN && echo -e "${YELLOW}Re-run without --dry-run to actually delete.${NC}"
