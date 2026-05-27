#!/bin/bash
# Bake semua au-color bodies dengan idle anim.
# Usage: bash tools/bake_all.sh

cd "$(dirname "$0")/.."

BLENDER="/e/blender/blender.exe"
COLORS=("blue" "brown" "cyan" "gray" "green" "lime" "orange" "pink" "purple" "red" "white" "yellow")
# Default: bake idle. Override: ANIM=... bash bake_all.sh
ANIM="${ANIM:-a2a-talk-idle-loop}"
SUFFIX="${SUFFIX:-idle}"

TOTAL=${#COLORS[@]}
OK=0
FAIL=0

for i in "${!COLORS[@]}"; do
    c="${COLORS[$i]}"
    n=$((i + 1))
    OUT="assets/vitaboy/au-${c}_${SUFFIX}.glb"
    echo ""
    echo "==[ $n/$TOTAL: au-${c} ]=========================="

    "$BLENDER" --background --python tools/bake_vitaboy.py -- \
        --mesh "au-${c}" --anim "$ANIM" --out "$OUT" 2>&1 | tail -3

    if [ -f "$OUT" ]; then
        size=$(stat -c '%s' "$OUT" 2>/dev/null || stat -f '%z' "$OUT")
        echo "  → ${OUT} (${size} bytes)"
        OK=$((OK + 1))
    else
        echo "  FAIL"
        FAIL=$((FAIL + 1))
    fi
done

echo ""
echo "========================================="
echo "BATCH DONE: OK=$OK  FAIL=$FAIL"
echo "Output: assets/vitaboy/"
ls -la assets/vitaboy/*.glb 2>/dev/null | awk '{print "  "$5"  "$9}'
