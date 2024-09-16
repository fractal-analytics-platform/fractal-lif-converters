from pathlib import Path

from lif_converters.lif_converter_compute_task import (
    lif_converter_compute_task,
)
from lif_converters.lif_plate_converter_init_task import lif_plate_converter_init_task


def test_basic_worflow(tmp_path):
    path = Path(__file__).parent / "data/Project_3D.lif"
    assert path.exists(), f"Path {path} does not exist"
    zarr_path = tmp_path

    parallelization_list = lif_plate_converter_init_task(
        [],
        zarr_dir=str(zarr_path),
        lif_files_path=str(path),
        num_levels=5,
        coarsening_xy=2.0,
        overwrite=True,
    )

    list_of_images = []
    for task_args in parallelization_list["parallelization_list"]:
        print(task_args["init_args"])
        list_updates = lif_converter_compute_task(
            zarr_url=task_args["zarr_url"], **task_args["init_args"]
        )
        list_of_images.extend(list_updates["image_list_updates"])

    # TODO add check on the zarr prduced
