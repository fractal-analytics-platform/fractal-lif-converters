from pathlib import Path

from fractal_lif_converters.wrappers import (
    LifPlateInputModel,
    LifSingleAcqInputModel,
    convert_lif_plate_to_omezarr,
    convert_lif_single_acq_to_omezarr,
)


def test_basic_worflow(tmp_path):
    path = Path(__file__).parent / "data/Project_3D.lif"
    assert path.exists(), f"Path {path} does not exist"
    convert_lif_plate_to_omezarr(
        zarr_dir=tmp_path / "plate", acquisitions=[LifPlateInputModel(path=str(path))]
    )
    convert_lif_single_acq_to_omezarr(
        zarr_dir=tmp_path / "scene",
        acquisitions=[LifSingleAcqInputModel(path=str(path))],
    )
