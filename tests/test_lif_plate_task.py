from pathlib import Path

import pytest

from fractal_lif_converters.common import image_in_plate_compute_task
from fractal_lif_converters.lif.plate.convert_lif_plate_init_task import (
    convert_lif_plate_init_task,
)

from .utils import DATA_DIR, run_converter_test

SNAPSHOT_DIR = DATA_DIR / "snapshots"


@pytest.mark.parametrize(
    "init_task_kwargs, snapshot_name",
    [
        (
            {"acquisitions": [{"path": str(DATA_DIR / "Project_3D.lif")}]},
            "lif_plate_default",
        ),
    ],
)
def test_lif_plate(
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
