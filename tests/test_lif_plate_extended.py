from pathlib import Path

import pytest

from fractal_lif_converters.common import image_in_plate_compute_task
from fractal_lif_converters.lif_plate.convert_lif_plate_init_task import (
    convert_lif_plate_init_task,
)

from .utils import run_converter_test

EXTENDED_DATA_DIR = Path(__file__).parent / "data-extended"
SNAPSHOT_DIR = EXTENDED_DATA_DIR / "Leica-LIF" / "snapshots"
RAW_DIR = EXTENDED_DATA_DIR / "Leica-LIF" / "raw"

_DATASETS: list[str] = []


@pytest.mark.extended
@pytest.mark.parametrize(
    "init_task_kwargs, snapshot_name",
    [
        (
            {"acquisitions": [{"path": str(RAW_DIR / f"{name}.lif")}]},
            f"{name}_plate",
        )
        for name in _DATASETS
    ],
)
def test_lif_plate_extended(
    tmp_path: Path,
    init_task_kwargs: dict,
    snapshot_name: str,
    update_snapshots: bool,
):
    run_converter_test(
        tmp_path=tmp_path,
        init_task_fn=convert_lif_plate_init_task,
        compute_task_fn=image_in_plate_compute_task,
        init_task_kwargs=init_task_kwargs,
        snapshot_path=SNAPSHOT_DIR / f"{snapshot_name}.yaml",
        update_snapshots=update_snapshots,
        output_type="plate",
    )
