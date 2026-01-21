#!/bin/bash
# Automated validation script for openbb_liquidity
# Run via cron: */30 * * * * /media/sam/1TB/openbb_liquidity/scripts/validate-automations.sh

cd /media/sam/1TB/openbb_liquidity

LOG_FILE="/tmp/openbb_validation_$(date +%Y%m%d).log"
DISCORD_WEBHOOK="${DISCORD_WEBHOOK_URL:-}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_passed=0
check_failed=0

validate() {
    local name="$1"
    local cmd="$2"

    if eval "$cmd" >/dev/null 2>&1; then
        log "✅ $name"
        ((check_passed++))
    else
        log "❌ $name FAILED"
        ((check_failed++))
    fi
}

log "=== Starting Validation ==="

# File structure
for f in CLAUDE.md .claude/validation/config.json .github/workflows/sync-planning.yml .planning/ROADMAP.md; do
    validate "File: $f" "[ -f '$f' ]"
done

# GitHub checks
validate "GitHub Secret" "gh secret list 2>/dev/null | grep -q GH_PROJECT_PAT"
validate "GitHub Issues >=35" "[ \$(gh issue list --state all --limit 100 --json number | jq length) -ge 35 ]"
validate "GitHub Milestones =10" "[ \$(gh api repos/gptcompany/openbb_liquidity/milestones | jq length) -eq 10 ]"
validate "Last Workflow Success" "gh run list --limit 1 --json conclusion | jq -e '.[0].conclusion == \"success\"'"

# Config checks
validate "GSD Config" "[ \$(jq -r '.mode' .planning/config.json) = 'yolo' ]"
validate "Validation Config" "[ \$(jq -r '.domain' .claude/validation/config.json) = 'finance' ]"

log "=== Results: $check_passed passed, $check_failed failed ==="

# Discord alert on failure
if [ "$check_failed" -gt 0 ] && [ -n "$DISCORD_WEBHOOK" ]; then
    curl -s -X POST "$DISCORD_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{\"content\": \"⚠️ **openbb_liquidity Validation Failed**\n$check_failed checks failed. See logs: $LOG_FILE\"}"
fi

exit $check_failed
