#!/bin/bash
# Automated validation script for openbb_liquidity
# Run via cron: */30 * * * * /media/sam/1TB/openbb_liquidity/scripts/validate-automations.sh
# Features: Auto-fix on failure + Discord alerts

cd /media/sam/1TB/openbb_liquidity

LOG_FILE="/tmp/openbb_validation_$(date +%Y%m%d).log"
DISCORD_WEBHOOK="${DISCORD_WEBHOOK_URL:-}"
SOPS_KEY="$HOME/.config/sops/age/keys.txt"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_passed=0
check_failed=0
fixes_applied=0

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

fix_and_retry() {
    local name="$1"
    local check_cmd="$2"
    local fix_cmd="$3"

    if ! eval "$check_cmd" >/dev/null 2>&1; then
        log "🔧 Fixing: $name"
        if eval "$fix_cmd" >/dev/null 2>&1; then
            log "✅ Fixed: $name"
            ((fixes_applied++))
            ((check_passed++))
        else
            log "❌ Fix failed: $name"
            ((check_failed++))
        fi
    else
        log "✅ $name"
        ((check_passed++))
    fi
}

log "=== Starting Validation (with auto-fix) ==="

# File structure (no auto-fix - critical files)
for f in CLAUDE.md .claude/validation/config.json .github/workflows/sync-planning.yml .planning/ROADMAP.md; do
    validate "File: $f" "[ -f '$f' ]"
done

# GitHub Secret - auto-fix from SOPS
fix_and_retry "GitHub Secret" \
    "gh secret list 2>/dev/null | grep -q GH_PROJECT_PAT" \
    "SOPS_AGE_KEY_FILE=$SOPS_KEY sops --input-type dotenv --output-type dotenv -d /media/sam/1TB/.env.enc 2>/dev/null | grep '^GH_PROJECT_PAT=' | cut -d= -f2 | gh secret set GH_PROJECT_PAT"

# GitHub Issues - auto-fix by triggering sync
fix_and_retry "GitHub Issues >=35" \
    "[ \$(gh issue list --state all --limit 100 --json number | jq length) -ge 35 ]" \
    "gh workflow run 'Sync Planning' && sleep 60"

# GitHub Milestones - auto-fix by triggering sync
fix_and_retry "GitHub Milestones =10" \
    "[ \$(gh api repos/gptcompany/openbb_liquidity/milestones | jq length) -eq 10 ]" \
    "gh workflow run 'Sync Planning' && sleep 60"

# Last Workflow - auto-fix by re-running
fix_and_retry "Last Workflow Success" \
    "gh run list --limit 1 --json conclusion | jq -e '.[0].conclusion == \"success\"'" \
    "gh workflow run 'Sync Planning' && sleep 120 && gh run list --limit 1 --json conclusion | jq -e '.[0].conclusion == \"success\"'"

# Config checks (no auto-fix - needs manual review)
validate "GSD Config" "[ \$(jq -r '.mode' .planning/config.json) = 'yolo' ]"
validate "Validation Config" "[ \$(jq -r '.domain' .claude/validation/config.json) = 'finance' ]"

log "=== Results: $check_passed passed, $check_failed failed, $fixes_applied auto-fixed ==="

# Discord alert
if [ -n "$DISCORD_WEBHOOK" ]; then
    if [ "$check_failed" -gt 0 ]; then
        curl -s -X POST "$DISCORD_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"content\": \"⚠️ **openbb_liquidity Validation Failed**\n❌ $check_failed checks failed\n🔧 $fixes_applied auto-fixes attempted\nSee: $LOG_FILE\"}"
    elif [ "$fixes_applied" -gt 0 ]; then
        curl -s -X POST "$DISCORD_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"content\": \"🔧 **openbb_liquidity Auto-Fixed**\n✅ $check_passed passed\n🔧 $fixes_applied issues auto-fixed\"}"
    fi
fi

exit $check_failed
