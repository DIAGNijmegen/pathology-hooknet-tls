#!/bin/bash
set -e

INPUT=$1
OUTPUT_WSI=$2
OUTPUT_MASK=$3

if [ -z "$INPUT" ] || [ -z "$OUTPUT_WSI" ] || [ -z "$OUTPUT_MASK" ]; then
    echo "Usage: run.sh <input.svs> <output.tif> <output_mask.tif>"
    exit 1
fi

echo "=== Step 1: Convert WSI ==="
python3 -u /opt/saveatlevel.py -i "$INPUT" -o "$OUTPUT_WSI"

echo "=== Step 2: Create mask ==="
python3 -u /opt/createmask.py -i "$OUTPUT_WSI" -o "$OUTPUT_MASK"

echo "=== Done ==="
