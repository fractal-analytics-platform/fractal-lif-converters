from pathlib import Path

import pytest
from ome_zarr_converters_tools.testing import run_converter_test

from fractal_lif_converters import convert_lif_image

from .utils import DATA_DIR

RAW_DIR = DATA_DIR / "Leica-LIF" / "raw"
SNAPSHOT_DIR = DATA_DIR / "Leica-LIF" / "snapshots"


@pytest.mark.parametrize(
    "init_task_kwargs, snapshot_name",
    [
        (
            {"acquisitions": [{"path": str(RAW_DIR / "hcs_2w1p3c5z1t.lif")}]},
            "img_2w1p3c5z1t",
        ),
    ],
)
def test_lif_image(
    tmp_path: Path,
    init_task_kwargs: dict,
    snapshot_name: str,
    update_snapshots: bool,
    converter_options,
):
    run_converter_test(
        tmp_path=tmp_path,
        api_fn=convert_lif_image,
        api_kwargs=init_task_kwargs,
        snapshot_path=SNAPSHOT_DIR / f"{snapshot_name}.json",
        update_snapshots=update_snapshots,
        converter_options=converter_options,
        output_type="single_image",
    )
