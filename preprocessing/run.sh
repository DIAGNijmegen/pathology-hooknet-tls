#!/bin/bash
set -e

INPUT=$1
OUTPUT_WSI=$2
OUTPUT_MASK=$3
TARGET_SPACING=${4:-0.5}
TOLERANCE=${5:-0.02}

if [ -z "$INPUT" ] || [ -z "$OUTPUT_WSI" ] || [ -z "$OUTPUT_MASK" ]; then
    echo "Usage: run.sh <input.svs> <output.tif> <output_mask.tif> [target_spacing] [tolerance]"
    echo "  target_spacing: Target spacing/mpp (default: 0.5)"
    echo "  tolerance: Tolerance for direct extraction (default: 0.02)"
    exit 1
fi

echo "=== Step 1: Convert WSI (target spacing: ${TARGET_SPACING} ± ${TOLERANCE}) ==="
python3 -u /opt/saveatlevel.py -i "$INPUT" -o "$OUTPUT_WSI" --target-spacing "$TARGET_SPACING" --tolerance "$TOLERANCE"

echo "=== Step 2: Create mask ==="
python3 -u /opt/createmask.py -i "$OUTPUT_WSI" -o "$OUTPUT_MASK"

echo "=== Done ==="
