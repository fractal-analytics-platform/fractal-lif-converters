from pathlib import Path

import pytest

from fractal_lif_converters.common import single_image_compute_task
from fractal_lif_converters.lif_single.convert_lif_single_acq_init_task import (
    convert_lif_single_acq_init_task,
)

from .utils import run_converter_test

EXTENDED_DATA_DIR = Path(__file__).parent / "data-extended"
SNAPSHOT_DIR = EXTENDED_DATA_DIR / "Leica-LIF" / "snapshots"
RAW_DIR = EXTENDED_DATA_DIR / "Leica-LIF" / "raw"
XLEF_SNAPSHOT_DIR = EXTENDED_DATA_DIR / "Leica-XLEF-LOF" / "snapshots"
XLEF_RAW_DIR = EXTENDED_DATA_DIR / "Leica-XLEF-LOF" / "raw"
XLEF_TIF_SNAPSHOT_DIR = EXTENDED_DATA_DIR / "Leica-XLEF-TIF" / "snapshots"
XLEF_TIF_RAW_DIR = EXTENDED_DATA_DIR / "Leica-XLEF-TIF" / "raw"

_DATASETS: list[str] = [
    "img_6p3c4z1t_STED_CustomShape_RectTiles",
    "img_4p3c1z1t_Stellaris_Positions",
    "img_4p3c6z1t_Stellaris_Mosaic",
    "img_1p1c1z1t_Thunder_Single",
    "img_4p3c1z1t_Thunder_SingleSeries",
    "img_7p3c1z1t_Falcon_MultiSeries",
    "img_1p3c1z1t_Stellaris_SingleSite_noNavigator",
]

_XLEF_DATASETS: list[str] = []

_XLEF_TIF_DATASETS: list[str] = [
    "img_1p3c24z1t_Mixed",
]


@pytest.mark.extended
@pytest.mark.parametrize(
    "init_task_kwargs, snapshot_path",
    [
        pytest.param(
            {"acquisitions": [{"path": str(RAW_DIR / f"{name}.lif")}]},
            SNAPSHOT_DIR / f"{name}_single_acq.yaml",
            id=name,
        )
        for name in _DATASETS
    ]
    + [
        pytest.param(
            {
                "acquisitions": [
                    {"path": str(XLEF_RAW_DIR / f"{name}" / f"{name}.xlef")}
                ]
            },
            XLEF_SNAPSHOT_DIR / f"{name}_single_acq.yaml",
            id=name,
        )
        for name in _XLEF_DATASETS
    ]
    + [
        pytest.param(
            {
                "acquisitions": [
                    {"path": str(XLEF_TIF_RAW_DIR / f"{name}" / f"{name}.xlef")}
                ]
            },
            XLEF_TIF_SNAPSHOT_DIR / f"{name}_single_acq.yaml",
            id=name,
        )
        for name in _XLEF_TIF_DATASETS
    ],
)
def test_lif_single_acq_extended(
    tmp_path: Path,
    init_task_kwargs: dict,
    snapshot_path: Path,
    update_snapshots: bool,
):
    run_converter_test(
        tmp_path=tmp_path,
        init_task_fn=convert_lif_single_acq_init_task,
        compute_task_fn=single_image_compute_task,
        init_task_kwargs=init_task_kwargs,
        snapshot_path=snapshot_path,
        update_snapshots=update_snapshots,
        output_type="single_image",
    )
