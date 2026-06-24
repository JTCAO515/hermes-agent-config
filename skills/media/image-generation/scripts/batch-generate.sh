#!/bin/bash
# Batch Image Generation with Seedream 5.0
# Usage: Edit the ITEMS array below, then run: bash scripts/batch-generate.sh
set -euo pipefail

OUTPUT_DIR="static/img"
API_URL="https://ark.cn-beijing.volces.com/api/v3/images/generations"

# ── EDIT THIS SECTION ──
# Keys = output filenames, Values = prompts
declare -A ITEMS
ITEMS[sample1]="Sample destination, beautiful landscape, sunny day, high quality travel photography"
ITEMS[sample2]="Another destination, city skyline, modern architecture, golden hour"

# ── RUN ──
for key in "${!ITEMS[@]}"; do
    prompt="${ITEMS[$key]}"
    outfile="${OUTPUT_DIR}/${key}.jpg"

    echo "=== Generating $key ==="

    response=$(curl -s --max-time 120 -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $VOLCENGINE_API_KEY" \
        -d "{
            \"model\": \"doubao-seedream-5-0-260128\",
            \"prompt\": \"${prompt}\",
            \"n\": 1,
            \"size\": \"1920x1920\"
        }")

    url=$(echo "$response" | python3 -c "
import sys, json
try:
    print(json.load(sys.stdin)['data'][0]['url'])
except:
    print('ERROR')
" 2>/dev/null || echo "ERROR")

    if [ "$url" = "ERROR" ]; then
        err_msg=$(echo "$response" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('error', {}).get('message', 'Unknown error'))
except:
    print('Parse failed')
" 2>/dev/null)
        echo "  FAILED: $err_msg"
        continue
    fi

    echo "  URL received, downloading..."
    curl -s -o "$outfile" --max-time 60 "$url"
    size=$(stat -c%s "$outfile" 2>/dev/null || stat -f%z "$outfile" 2>/dev/null || echo "?")
    echo "  Saved: $(basename $outfile) ($size bytes)"

    # Rate limit: 5 seconds between requests
    sleep 5
done

echo "=== Batch complete ==="
ls -lh "${OUTPUT_DIR}"/${!ITEMS[*]} 2>/dev/null | head -5
