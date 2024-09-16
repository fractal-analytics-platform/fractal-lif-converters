from pathlib import Path

from lif_converters.converter_wrapper import lif_plate_converter, lif_scene_converter


def test_basic_worflow(tmp_path):
    path = Path(__file__).parent / "data/Project_3D.lif"
    assert path.exists(), f"Path {path} does not exist"
    lif_plate_converter(zarr_dir=tmp_path / "plate", lif_files_path=path)
    lif_scene_converter(zarr_dir=tmp_path / "scene", lif_files_path=path)
