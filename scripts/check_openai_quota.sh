#!/usr/bin/env bash
# Probe whether OPENAI_API_KEY is valid and has available quota.
#
# Usage:
#   OPENAI_API_KEY=sk-... scripts/check_openai_quota.sh [model]
#
# Exit codes:
#   0  quota OK
#   1  insufficient_quota (out of credits / over spending cap)
#   2  rate_limit_exceeded (temporary throttle)
#   3  invalid_api_key (401)
#   4  network / unexpected error
#   5  OPENAI_API_KEY not set

set -u

MODEL="${1:-gpt-4o-mini}"

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "ERROR: OPENAI_API_KEY is not set" >&2
  exit 5
fi

TMP_BODY=$(mktemp)
trap 'rm -f "$TMP_BODY"' EXIT

HTTP_CODE=$(curl -sS -o "$TMP_BODY" -w "%{http_code}" \
  https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"${MODEL}\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_completion_tokens\":1}" \
  2>/dev/null) || {
  echo "ERROR: network failure reaching api.openai.com" >&2
  exit 4
}

ERROR_CODE=$(python3 -c "
import json, sys
try:
    d = json.load(open('$TMP_BODY'))
    print(d.get('error', {}).get('code') or '')
except Exception:
    print('')
" 2>/dev/null)

ERROR_MSG=$(python3 -c "
import json, sys
try:
    d = json.load(open('$TMP_BODY'))
    print(d.get('error', {}).get('message') or '')
except Exception:
    print('')
" 2>/dev/null)

case "$HTTP_CODE" in
  200)
    echo "OK    [HTTP 200] model=${MODEL} — quota available"
    exit 0
    ;;
  401)
    echo "FAIL  [HTTP 401] invalid_api_key — key is bad, revoked, or wrong project"
    [[ -n "$ERROR_MSG" ]] && echo "      ${ERROR_MSG}"
    exit 3
    ;;
  429)
    case "$ERROR_CODE" in
      insufficient_quota)
        echo "FAIL  [HTTP 429] insufficient_quota — add credits or raise spending cap"
        echo "      https://platform.openai.com/account/billing"
        exit 1
        ;;
      rate_limit_exceeded|*)
        echo "WARN  [HTTP 429] ${ERROR_CODE:-rate_limit_exceeded} — temporary throttle, retry shortly"
        [[ -n "$ERROR_MSG" ]] && echo "      ${ERROR_MSG}"
        exit 2
        ;;
    esac
    ;;
  404)
    echo "FAIL  [HTTP 404] model_not_found — '${MODEL}' is not available to this key"
    [[ -n "$ERROR_MSG" ]] && echo "      ${ERROR_MSG}"
    exit 4
    ;;
  *)
    echo "FAIL  [HTTP ${HTTP_CODE}] unexpected"
    [[ -n "$ERROR_MSG" ]] && echo "      ${ERROR_MSG}"
    exit 4
    ;;
esac
