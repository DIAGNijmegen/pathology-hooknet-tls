"""
Create a tissue-background mask from a converted tif file.

Uses ASAP (multiresolutionimageinterface) to read and write the image.
"""

import argparse
import os
import sys

import multiresolutionimageinterface as mir
import numpy as np
from skimage import color
from skimage.filters import threshold_otsu
from skimage.morphology import remove_small_holes, remove_small_objects
from skimage.transform import resize


def _find_best_level(image, target_spacing, base_spacing):
    """Return the level index whose spacing is closest to target_spacing."""
    best_level = 0
    best_diff = float("inf")
    for level in range(image.getNumberOfLevels()):
        level_spacing = base_spacing * image.getLevelDownsample(level)
        diff = abs(level_spacing - target_spacing)
        if diff < best_diff:
            best_diff = diff
            best_level = level
    return best_level


def create_mask(
    input_path,
    output_path,
    processing_spacing=8.0,
    mask_spacing=2.0,
    tile_size=512,
    min_size=64,
):
    reader = mir.MultiResolutionImageReader()
    image = reader.open(input_path)
    if image is None:
        raise RuntimeError(f"Failed to open: {input_path}")

    spacings = image.getSpacing()
    if not spacings:
        raise RuntimeError("Image has no spacing/mpp metadata.")
    base_spacing = spacings[0]
    print(f"Base spacing: {base_spacing:.4f}")

    # ---- read whole slide at processing level ----
    proc_level = _find_best_level(image, processing_spacing, base_spacing)
    real_proc_spacing = base_spacing * image.getLevelDownsample(proc_level)
    print(f"Processing level {proc_level}, actual spacing ~{real_proc_spacing:.3f}")

    width, height = image.getLevelDimensions(proc_level)
    slide = image.getUCharPatch(0, 0, width, height, proc_level)
    print(f"Slide shape: {slide.shape}")

    # ---- create mask ----
    grey = color.rgb2gray(slide)
    mask = grey < threshold_otsu(grey)
    mask = remove_small_objects(mask, min_size=min_size)
    mask = remove_small_holes(mask, area_threshold=min_size)

    # ---- determine output mask level spacing ----
    mask_level = _find_best_level(image, mask_spacing, base_spacing)
    real_mask_spacing = base_spacing * image.getLevelDownsample(mask_level)
    print(f"Mask output spacing ~{real_mask_spacing:.3f}")

    upsample_ratio = real_proc_spacing / real_mask_spacing

    # ---- upsample mask (nearest-neighbour) ----
    out_h = int(round(height * upsample_ratio))
    out_w = int(round(width * upsample_ratio))
    mask_upscaled = resize(
        mask, (out_h, out_w), order=0, preserve_range=True, anti_aliasing=False
    ).astype(np.uint8)  # values: 0 or 1
    print(f"Upscaled mask shape: {mask_upscaled.shape}")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    writer = mir.MultiResolutionImageWriter()
    if writer.openFile(output_path) != 0:
        raise RuntimeError(f"Failed to open for writing: {output_path}")

    writer.setDataType(mir.DataType_UChar)
    writer.setColorType(mir.ColorType_Monochrome)
    writer.setCompression(mir.Compression_LZW)
    writer.setInterpolation(mir.Interpolation_NearestNeighbor)
    writer.setTileSize(tile_size)
    writer.writeImageInformation(out_w, out_h)

    spacing_vec = mir.vector_double()
    spacing_vec.push_back(real_mask_spacing)
    spacing_vec.push_back(real_mask_spacing)
    writer.setSpacing(spacing_vec)

    for row in range(0, out_h, tile_size):
        for col in range(0, out_w, tile_size):
            tile_w = min(tile_size, out_w - col)
            tile_h = min(tile_size, out_h - row)
            tile = mask_upscaled[row:row + tile_h, col:col + tile_w]

            if tile_w < tile_size or tile_h < tile_size:
                padded = np.zeros((tile_size, tile_size), dtype=np.uint8)
                padded[:tile_h, :tile_w] = tile
                tile = padded

            writer.writeBaseImagePartToLocation(tile.flatten(), col, row)

    writer.finishImage()
    print(f"Saved mask: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Create tissue-background mask from converted tif"
    )
    parser.add_argument("-i", "--input", required=True, help="Input tif path")
    parser.add_argument("-o", "--output", required=True, help="Output mask tif path")
    parser.add_argument(
        "--processing-spacing",
        type=float,
        default=8.0,
        help="Spacing (µm/px) used for mask computation (default: 8.0)",
    )
    parser.add_argument(
        "--mask-spacing",
        type=float,
        default=2.0,
        help="Output mask spacing (µm/px) (default: 2.0)",
    )
    parser.add_argument("-t", "--tile-size", type=int, default=512, help="Tile size")
    parser.add_argument("--min-size", type=int, default=64, help="Min size for remove_small_objects/holes (default: 64)")
    parser.add_argument("-w", "--overwrite", action="store_true", help="Overwrite existing output")

    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: Input not found: {args.input}")
        return 1

    if os.path.exists(args.output) and not args.overwrite:
        print(f"Error: Output exists: {args.output}. Use -w to overwrite.")
        return 1

    create_mask(
        args.input,
        args.output,
        args.processing_spacing,
        args.mask_spacing,
        args.tile_size,
        args.min_size,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
