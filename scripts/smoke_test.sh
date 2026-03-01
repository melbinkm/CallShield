#!/usr/bin/env bash
set -euo pipefail

API_URL="${1:-http://localhost:8000}"
PASS=0
FAIL=0

echo "CallShield Smoke Tests"
echo "Target: $API_URL"
echo "========================"

# Test 1: Health check
echo -n "Test 1: GET /api/health ... "
HTTP_CODE=$(curl -sf -o /tmp/health_response.json -w "%{http_code}" "$API_URL/api/health" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "PASS (HTTP $HTTP_CODE)"
    PASS=$((PASS + 1))
else
    echo "FAIL (HTTP $HTTP_CODE)"
    FAIL=$((FAIL + 1))
fi

# Test 2: Transcript analysis - IRS scam should score > 0.5
echo -n "Test 2: POST /api/analyze/transcript (IRS scam) ... "
IRS_TRANSCRIPT="This is Officer Johnson from the IRS. A federal arrest warrant has been issued in your name. You owe \$4,782 in back taxes. You must purchase Google Play gift cards immediately or officers will be sent to arrest you within 45 minutes. This is your final warning."

RESPONSE=$(curl -sf -X POST "$API_URL/api/analyze/transcript" \
    -H "Content-Type: application/json" \
    -d "{\"transcript\": \"$IRS_TRANSCRIPT\"}" 2>/dev/null || echo "CURL_FAILED")

if [ "$RESPONSE" = "CURL_FAILED" ]; then
    echo "FAIL (request failed)"
    FAIL=$((FAIL + 1))
else
    # Validate response has required fields and score > 0.5
    RESULT=$(echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
score = data.get('combined_score', 0)
has_id = 'id' in data
print(f'score={score:.2f} has_id={has_id}')
if score > 0.5 and has_id:
    sys.exit(0)
else:
    sys.exit(1)
" 2>/dev/null) && TEST2_OK=true || TEST2_OK=false

    if [ "$TEST2_OK" = true ]; then
        echo "PASS ($RESULT)"
        PASS=$((PASS + 1))
    else
        echo "FAIL ($RESULT)"
        FAIL=$((FAIL + 1))
    fi
fi

# Test 3: Root endpoint
echo -n "Test 3: GET / ... "
HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "$API_URL/" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "PASS (HTTP $HTTP_CODE)"
    PASS=$((PASS + 1))
else
    echo "FAIL (HTTP $HTTP_CODE)"
    FAIL=$((FAIL + 1))
fi

# Summary
echo "========================"
echo "Results: $PASS passed, $FAIL failed"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
echo "All tests passed!"
