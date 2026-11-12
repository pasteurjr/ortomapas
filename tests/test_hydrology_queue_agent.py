from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from backend.agents import hydrology_queue_agent as queue_module
from backend.agents.hydrology_queue_agent import QueuedHydrologyAnalysisAgent


class FakeCursor:
    def __init__(self, source):
        self.source = source
        self.result = None

    def execute(self, sql, params):
        self.result = self.source if "SELECT * FROM ortomapas" in sql else {"id": 501}

    def fetchone(self):
        return self.result


class FakeConnection:
    def __init__(self, source):
        self.cursor_value = FakeCursor(source)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def cursor(self, **_kwargs):
        return self.cursor_value


@pytest.mark.parametrize("operation", ["flow_direction", "flow_accumulation", "twi"])
def test_queued_hydrology_raster_products_run_and_publish(tmp_path, monkeypatch, operation):
    dem_path = tmp_path / "known_metric_dtm.tif"
    rows, cols = np.mgrid[0:48, 0:64]
    dem = (300 - rows * 0.8 - cols * 0.4).astype("float32")
    with rasterio.open(
        dem_path,
        "w",
        driver="GTiff",
        width=cols.shape[1],
        height=rows.shape[0],
        count=1,
        dtype="float32",
        crs="EPSG:32617",
        transform=from_origin(500000, 7000000, 2, 2),
        nodata=-9999,
    ) as target:
        target.write(dem, 1)

    source = {"id": 41, "projeto_id": 9, "tipo": "dtm", "caminho_arquivo": str(dem_path)}
    monkeypatch.setattr(queue_module, "get_connection", lambda: FakeConnection(source))
    monkeypatch.setattr(queue_module, "data_path", lambda value: Path(value))
    monkeypatch.setattr(queue_module, "ANALISES_DIR", str(tmp_path / "published"))
    published = {}

    def capture_publish(_source, name, output, details, parameters, **_kwargs):
        published.update(operation=name, output=Path(output), details=details, parameters=parameters)
        return {"status": "concluida"}

    monkeypatch.setattr(queue_module, "publish_hydrology", capture_publish)
    task = {
        "id": 700 + len(operation),
        "ortomapa_id": 41,
        "parametros": {"hydro_type": operation, "_analysis_id": 501, "_project_id": 9, "_user_id": 2},
    }

    result = QueuedHydrologyAnalysisAgent().execute(task)

    assert result["status"] == "concluida"
    assert published["operation"] == operation
    assert published["output"].is_file()
    assert published["details"]["working_grid"]["working_shape"] == [48, 64]
    with rasterio.open(published["output"]) as dataset:
        assert dataset.crs.to_epsg() == 32617
        values = dataset.read(1, masked=True).compressed()
    assert values.size > 0 and np.isfinite(values).all()
    if operation == "flow_direction":
        assert set(np.unique(values)).issubset({1, 2, 4, 8, 16, 32, 64, 128})
    elif operation == "flow_accumulation":
        assert values.min() >= 1 and values.max() > values.min()
