"""
Optimized script to save WSI at ~0.5 mpp spacing.
Intelligently selects direct extraction or two-step approach.
Only requires ASAP's multiresolutionimageinterface.
"""

import multiresolutionimageinterface as mir
import numpy as np
import argparse
import os
import sys
import tempfile


def find_best_level(image, target_spacing, base_spacing, tolerance=0.02):
    """
    Find the level closest to target_spacing.
    Returns (level_index, actual_spacing, within_tolerance)
    """
    best_level = 0
    best_diff = float("inf")
    best_spacing = None

    for level in range(image.getNumberOfLevels()):
        level_spacing = base_spacing * image.getLevelDownsample(level)
        diff = abs(level_spacing - target_spacing)
        if diff < best_diff:
            best_diff = diff
            best_level = level
            best_spacing = level_spacing

    within_tolerance = best_diff <= tolerance
    return best_level, best_spacing, within_tolerance


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
    parser = argparse.ArgumentParser(
        description="Save WSI at ~0.5 mpp. Uses direct extraction if available, otherwise two-step approach."
    )
    parser.add_argument("-i", "--input", required=True, help="Input image path")
    parser.add_argument("-o", "--output", required=True, help="Output image path")
    parser.add_argument(
        "--target-spacing",
        type=float,
        default=0.5,
        help="Target spacing/mpp (default: 0.5)",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.02,
        help="Tolerance for direct extraction (default: 0.02, i.e., 0.48-0.52 for target 0.5)",
    )
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

    # Open input to analyze levels
    reader = mir.MultiResolutionImageReader()
    image = reader.open(args.input)
    if image is None:
        print(f"Error: Failed to open: {args.input}")
        return 1

    spacing = image.getSpacing()
    if not spacing or spacing[0] == 0:
        print("Error: Image has no spacing/mpp metadata.")
        return 1

    base_spacing = spacing[0]
    num_levels = image.getNumberOfLevels()

    print(f"Input: {args.input}")
    print(f"Base spacing: {base_spacing:.4f} mpp")
    print(f"Number of levels: {num_levels}")
    print(f"Target spacing: {args.target_spacing} ± {args.tolerance} mpp")
    print()

    # Print all available levels
    print("Available levels:")
    for level in range(num_levels):
        level_spacing = base_spacing * image.getLevelDownsample(level)
        dims = image.getLevelDimensions(level)
        print(f"  Level {level}: {dims[0]}x{dims[1]}, spacing={level_spacing:.4f} mpp")
    print()

    # Find best level for target spacing
    best_level, actual_spacing, within_tolerance = find_best_level(
        image, args.target_spacing, base_spacing, args.tolerance
    )

    if within_tolerance:
        # Direct extraction
        print(f"✓ Direct extraction: Level {best_level} (spacing={actual_spacing:.4f} mpp) is within tolerance")
        print(f"Extracting level {best_level} -> {args.output}")
        save_level(args.input, args.output, level=best_level, tile_size=args.tile_size, jpeg_quality=args.quality)
    else:
        # Two-step approach: extract level 0, then extract target from its pyramid
        print(f"✗ No level within tolerance. Using two-step approach.")

        # Level 0 always has base spacing
        intermediate_level = 0
        intermediate_spacing = base_spacing

        print(f"Step 1: Extract level {intermediate_level} (spacing={intermediate_spacing:.4f} mpp) -> intermediate")

        basename = os.path.splitext(os.path.basename(args.input))[0]
        intermediate = os.path.join(tempfile.gettempdir(), f"{basename}_level{intermediate_level}_tmp.tif")

        save_level(
            args.input,
            intermediate,
            level=intermediate_level,
            tile_size=args.tile_size,
            jpeg_quality=args.quality,
        )

        # Open intermediate and find level for target spacing
        reader2 = mir.MultiResolutionImageReader()
        image2 = reader2.open(intermediate)
        if image2 is None:
            print(f"Error: Failed to open intermediate: {intermediate}")
            return 1

        intermediate_base_spacing = image2.getSpacing()[0]
        final_level, final_spacing, _ = find_best_level(
            image2, args.target_spacing, intermediate_base_spacing, tolerance=float('inf')
        )

        print(f"Step 2: Extract level {final_level} (spacing={final_spacing:.4f} mpp) from intermediate -> output")
        save_level(
            intermediate,
            args.output,
            level=final_level,
            tile_size=args.tile_size,
            jpeg_quality=args.quality,
        )

        if not args.keep_intermediate:
            os.remove(intermediate)
            print(f"Cleaned up: {intermediate}")
        else:
            print(f"Kept intermediate: {intermediate}")

    print(f"Done: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
