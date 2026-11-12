import numpy as np
import rasterio
from rasterio.enums import ColorInterp
from rasterio.transform import from_origin

from backend.tools.change_detection import change_statistics, detect_changes


def _write_rgba(path, data):
    profile = {
        "driver": "GTiff", "width": data.shape[2], "height": data.shape[1],
        "count": 4, "dtype": "uint8", "crs": "EPSG:32617",
        "transform": from_origin(500000, 4500000, 0.5, 0.5),
    }
    with rasterio.open(path, "w", **profile) as dataset:
        dataset.write(data)
        dataset.colorinterp = (ColorInterp.red, ColorInterp.green, ColorInterp.blue, ColorInterp.alpha)


def test_rgb_change_ignores_alpha_and_masks_nonoverlapping_valid_pixels(tmp_path):
    before = np.zeros((4, 32, 32), dtype=np.uint8)
    before[0] = 30
    before[1] = 80
    before[2] = 120
    before[3] = 255
    before[3, 5, 5] = 0

    after = before.copy()
    after[:3, 10:20, 10:20] = 255 - after[:3, 10:20, 10:20]
    after[3, 15, 15] = 0

    before_path = tmp_path / "before.tif"
    after_path = tmp_path / "after.tif"
    output_path = tmp_path / "change.tif"
    _write_rgba(before_path, before)
    _write_rgba(after_path, after)

    detect_changes(str(before_path), str(after_path), str(output_path), threshold=0.15 * 255)
    statistics = change_statistics(str(output_path))

    assert statistics["total_pixels"] == 32 * 32 - 2
    assert statistics["changed_pixels"] == 99
    assert statistics["area_changed_m2"] == 24.75
    with rasterio.open(output_path) as result:
        assert set(np.unique(result.read(1))) == {0, 255}
        assert result.dataset_mask()[5, 5] == 0
        assert result.dataset_mask()[15, 15] == 0
