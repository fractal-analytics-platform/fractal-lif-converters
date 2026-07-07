from pathlib import Path

import pytest
from ome_zarr_converters_tools.testing import run_converter_test

from fractal_lif_converters import convert_lif_plate

EXTENDED_DATA_DIR = Path(__file__).parent / "data-extended"
LIF_SNAPSHOT_DIR = EXTENDED_DATA_DIR / "Leica-LIF" / "snapshots"
LIF_RAW_DIR = EXTENDED_DATA_DIR / "Leica-LIF" / "raw"
XLEF_SNAPSHOT_DIR = EXTENDED_DATA_DIR / "Leica-XLEF-LOF" / "snapshots"
XLEF_RAW_DIR = EXTENDED_DATA_DIR / "Leica-XLEF-LOF" / "raw"
XLEF_TIF_SNAPSHOT_DIR = EXTENDED_DATA_DIR / "Leica-XLEF-TIF" / "snapshots"
XLEF_TIF_RAW_DIR = EXTENDED_DATA_DIR / "Leica-XLEF-TIF" / "raw"

_DATASETS: list[str] = [
    "hcs_2w4p3c1z1t_Falcon_Grid",
    "hcs_2w4p3c1z1t_Falcon_MultiScan",
    "hcs_2w4p3c5z1t_Falcon_Grid",
    "hcs_2w4p3c1z3t_Falcon_TimeSeries",
    "hcs_2w2p3c4z1t_STED_Mosaic",
    "hcs_2w2p3c4z1t_STED_Positions",
    "hcs_2w6p3c1z1t_STED_Mosaic",
    "hcs_2w6p3c1z1t_STED_Positions",
    "hcs_2w4p3c1z1t_Stellaris_CustomPositions",
    "hcs_2w6p3c1z1t_Stellaris_Mosaic",
    "hcs_2w6p3c1z1t_Stellaris_Positions",
    "hcs_2w1p3c1z1t_Thunder_Mosaic",
    "hcs_2w1p3c1z1t_Thunder_Positions",
    "hcs_2w4p3c1z1t_Thunder_CustomPositions",
    "hcs_2w4p3c1z1t_Thunder_CustomShape",
    "hcs_2w6p3c1z1t_Thunder_Mosaic",
    "hcs_2w6p3c1z1t_Thunder_Positions",
    "hcs_2w6p3c5z1t_Thunder_Mosaic",
    "hcs_2w6p3c5z4t_Thunder_Mosaic",
]

_XLEF_DATASETS: list[str] = [
    "hcs_2w6p2c1z1t_Mosaic",
    "hcs_2w6p2c3z1t_Mosaic",
    "hcs_2w6p2c3z2t_Positions",
    "hcs_2w6p2c3z2t_Mosaic",
    # Non-deterministic bug in the LIF reader
    # "hcs_2w6p2c1z1t_Positions",
    # "hcs_2w6p2c3z1t_Positions",
]

_XLEF_TIF_DATASETS: list[str] = [
    "hcs_2w1p1c1z1t_Positions",
    "hcs_2w3p1c1z1t_Positions",
    "hcs_2w6p1c1z1t_Mosaic",
    "hcs_2w3p3c1z1t_Positions",
    "hcs_2w6p3c1z1t_Mosaic",
    "hcs_2w3p3c8z1t_Positions",
    "hcs_2w6p3c8z1t_Mosaic",
    "hcs_2w3p3c8z2t_Positions",
    "hcs_2w6p3c8z2t_Mosaic_FocusMap",
    "hcs_2w3p3c1z1t_Mixed",
    "hcs_2w6p2c1z1t_Mosaic_TIF",
    "hcs_2w6p2c3z1t_Mosaic_TIF",
    "hcs_2w6p2c3z2t_Positions_TIF",
    # Non-deterministic bug in the LIF reader
    # "hcs_2w6p2c1z1t_Positions_TIF",
    # "hcs_2w6p2c3z1t_Positions_TIF",
]


@pytest.mark.extended
@pytest.mark.parametrize(
    "init_task_kwargs, snapshot_path",
    [
        pytest.param(
            {"acquisitions": [{"path": str(LIF_RAW_DIR / f"{name}.lif")}]},
            LIF_SNAPSHOT_DIR / f"{name}.json",
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
            XLEF_SNAPSHOT_DIR / f"{name}.json",
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
            XLEF_TIF_SNAPSHOT_DIR / f"{name}.json",
            id=name,
        )
        for name in _XLEF_TIF_DATASETS
    ],
)
def test_lif_plate_extended(
    tmp_path: Path,
    init_task_kwargs: dict,
    snapshot_path: Path,
    update_snapshots: bool,
    converter_options,
):
    run_converter_test(
        tmp_path=tmp_path,
        api_fn=convert_lif_plate,
        api_kwargs=init_task_kwargs,
        snapshot_path=snapshot_path,
        update_snapshots=update_snapshots,
        converter_options=converter_options,
        output_type="plate",
    )
