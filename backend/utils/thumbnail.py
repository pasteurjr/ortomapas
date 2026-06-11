"""
Thumbnail generation for GeoTIFF files.
"""

import logging
from typing import Tuple

import numpy as np
import rasterio
from PIL import Image

logger = logging.getLogger(__name__)


def generate_thumbnail(
    input_path: str,
    output_path: str,
    size: Tuple[int, int] = (512, 512),
) -> str:
    """
    Create a PNG thumbnail from a GeoTIFF file using rasterio + PIL.

    Args:
        input_path: Path to the source GeoTIFF file.
        output_path: Path where the PNG thumbnail will be saved.
        size: Thumbnail dimensions as (width, height).

    Returns:
        The output_path on success.
    """
    try:
        with rasterio.open(input_path) as dataset:
            # Calculate the overview level (decimation factor) for fast reading
            height, width = dataset.height, dataset.width
            max_dim = max(height, width)
            # Read at a reduced resolution for speed
            out_shape_h = min(size[1], height)
            out_shape_w = min(size[0], width)

            band_count = dataset.count

            if band_count >= 3:
                # Read RGB bands
                data = dataset.read(
                    [1, 2, 3],
                    out_shape=(3, out_shape_h, out_shape_w),
                )
                # Transpose to (H, W, C) for PIL
                img_array = np.transpose(data, (1, 2, 0))
            elif band_count == 1:
                # Single band — create grayscale
                data = dataset.read(
                    1,
                    out_shape=(out_shape_h, out_shape_w),
                )
                img_array = data
            else:
                # 2 bands — use first band as grayscale
                data = dataset.read(
                    1,
                    out_shape=(out_shape_h, out_shape_w),
                )
                img_array = data

            # Handle nodata by replacing with 0
            nodata = dataset.nodata
            if nodata is not None:
                img_array = np.where(img_array == nodata, 0, img_array)

            # Normalize to 0-255 uint8 if not already
            if img_array.dtype != np.uint8:
                arr_min = np.nanmin(img_array)
                arr_max = np.nanmax(img_array)
                if arr_max > arr_min:
                    img_array = ((img_array - arr_min) / (arr_max - arr_min) * 255).astype(
                        np.uint8
                    )
                else:
                    img_array = np.zeros_like(img_array, dtype=np.uint8)

            # Create PIL image
            if img_array.ndim == 3:
                img = Image.fromarray(img_array, mode="RGB")
            else:
                img = Image.fromarray(img_array, mode="L")

            # Resize to requested thumbnail size
            img = img.resize(size, Image.LANCZOS)
            img.save(output_path, format="PNG")

            logger.info(f"Thumbnail generated: {output_path}")
            return output_path

    except Exception as e:
        logger.error(f"Error generating thumbnail for {input_path}: {e}")
        raise
