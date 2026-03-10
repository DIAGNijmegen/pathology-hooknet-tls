"""
Minimal standalone script to save image at level 0, then level 1.
Only requires ASAP's multiresolutionimageinterface.
"""

import multiresolutionimageinterface as mir
import numpy as np
import argparse
import os
import sys
import tempfile


def save_level(input_path, output_path, level, tile_size=512, jpeg_quality=80):
    """
    Extract a single level from input image and save as new tiled TIFF.
    """
    # Open input image
    reader = mir.MultiResolutionImageReader()
    image = reader.open(input_path)
    if image is None:
        raise RuntimeError(f"Failed to open: {input_path}")

    # Get level info
    dims = image.getLevelDimensions(level)
    spacing = image.getSpacing()
    downsample = image.getLevelDownsample(level)

    width, height = dims
    level_spacing = spacing[0] * downsample if spacing else None

    print(f"  Level {level}: {width}x{height}, spacing={level_spacing}")

    # Create writer
    writer = mir.MultiResolutionImageWriter()
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    if writer.openFile(output_path) != 0:
        raise RuntimeError(f"Failed to open for writing: {output_path}")

    # Configure writer
    writer.setDataType(mir.DataType_UChar)
    writer.setColorType(mir.ColorType_RGB)
    writer.setCompression(mir.Compression_JPEG)
    writer.setInterpolation(mir.Interpolation_Linear)
    writer.setTileSize(tile_size)
    writer.setJPEGQuality(jpeg_quality)
    writer.writeImageInformation(width, height)

    if level_spacing:
        spacing_vec = mir.vector_double()
        spacing_vec.push_back(level_spacing)
        spacing_vec.push_back(level_spacing)
        writer.setSpacing(spacing_vec)

    # Write tiles
    for row in range(0, height, tile_size):
        for col in range(0, width, tile_size):
            # Read tile from source level
            tile_w = min(tile_size, width - col)
            tile_h = min(tile_size, height - row)
            tile = image.getUCharPatch(int(col * downsample), int(row * downsample), tile_w, tile_h, level)

            # Pad if needed
            if tile_w < tile_size or tile_h < tile_size:
                padded = np.zeros((tile_size, tile_size, 3), dtype=np.uint8)
                padded[:tile_h, :tile_w, :] = tile
                tile = padded

            writer.writeBaseImagePartToLocation(tile.flatten(), col, row)

    writer.finishImage()
    print(f"  Saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Save level 0, then extract final level from that output")
    parser.add_argument("-i", "--input", required=True, help="Input image path")
    parser.add_argument("-o", "--output", required=True, help="Output image path")
    parser.add_argument("-l", "--level", type=int, default=1, help="Final level to extract (default: 1)")
    parser.add_argument("-q", "--quality", type=int, default=90, help="JPEG quality (1-100)")
    parser.add_argument("-t", "--tile-size", type=int, default=512, help="Tile size")
    parser.add_argument("-w", "--overwrite", action="store_true", help="Overwrite existing")
    parser.add_argument("--keep-intermediate", action="store_true", help="Keep intermediate file")

    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: Input not found: {args.input}")
        return 1

    if os.path.exists(args.output) and not args.overwrite:
        print(f"Error: Output exists: {args.output}. Use -w to overwrite.")
        return 1

    # Intermediate file path
    basename = os.path.splitext(os.path.basename(args.input))[0]
    intermediate = os.path.join(tempfile.gettempdir(), f"{basename}_level0_tmp.tif")

    print(f"Step 1: Extract level 0 -> intermediate")
    save_level(args.input, intermediate, level=0, tile_size=args.tile_size, jpeg_quality=args.quality)

    print(f"Step 2: Extract level {args.level} from intermediate -> output")
    save_level(intermediate, args.output, level=args.level, tile_size=args.tile_size, jpeg_quality=args.quality)

    if not args.keep_intermediate:
        os.remove(intermediate)
        print(f"Cleaned up: {intermediate}")
    else:
        print(f"Kept intermediate: {intermediate}")

    print(f"Done: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
