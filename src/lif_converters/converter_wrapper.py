"""Utility for running the init and compute tasks with a single function call."""

from pathlib import Path

from lif_converters.lif_converter_compute_task import (
    lif_converter_compute_task,
)
from lif_converters.lif_plate_converter_init_task import lif_plate_converter_init_task
from lif_converters.lif_scene_converter_init_task import (
    lif_scene_converter_init_task,
)


def lif_plate_converter(
    zarr_dir: Path | str,
    lif_files_path: Path | str,
    num_levels: int = 5,
    coarsening_xy: int = 2,
    overwrite: bool = False,
):
    """Convert LIF files to an OME-Zarr Ngff Plate.

    Args:
        zarr_dir (Path | str): Output path to save the OME-Zarr file.
        lif_files_path (Path | str): Input path to the LIF file,
            or a folder containing LIF files.
        num_levels (int): The number of resolution levels. Defaults to 5.
        coarsening_xy (float): The scaling factor for the xy axes. Defaults to 2.0.
        overwrite (bool): If True, the zarr store will be overwritten

    """
    parallelization_list = lif_plate_converter_init_task(
        zarr_urls=[],
        zarr_dir=str(zarr_dir),
        lif_files_path=str(lif_files_path),
        num_levels=num_levels,
        coarsening_xy=coarsening_xy,
        overwrite=overwrite,
    )

    list_of_images = []
    for task_args in parallelization_list["parallelization_list"]:
        list_updates = lif_converter_compute_task(
            zarr_url=task_args["zarr_url"], init_args=task_args["init_args"]
        )
        list_of_images.extend(list_updates["image_list_updates"])


def lif_scene_converter(
    zarr_dir: Path | str,
    lif_files_path: Path | str,
    scene_name: str | None = None,
    num_levels: int = 5,
    coarsening_xy: float = 2.0,
    overwrite: bool = False,
):
    """Convert LIF files to an OME-Zarr Ngff Image.

    Args:
        zarr_dir (Path | str): Output path to save the OME-Zarr file.
        lif_files_path (Path | str): Input path to the LIF file,
            or a folder containing LIF files.
        scene_name (str | None): Name of the scene to convert. If None all scenes in the
            lif file will will converted. If a folder of lif files is provided, the
            scene_nane will be converted from each file.
        num_levels (int): The number of resolution levels. Defaults to 5.
        coarsening_xy (float): The scaling factor for the xy axes. Defaults to 2.0.
        overwrite (bool): If True, the zarr store will be overwritten

    """
    parallelization_list = lif_scene_converter_init_task(
        zarr_urls=[],
        zarr_dir=str(zarr_dir),
        lif_files_path=str(lif_files_path),
        scene_name=scene_name,
        num_levels=num_levels,
        coarsening_xy=coarsening_xy,
        overwrite=overwrite,
    )

    list_of_images = []
    for task_args in parallelization_list["parallelization_list"]:
        list_updates = lif_converter_compute_task(
            zarr_url=task_args["zarr_url"], init_args=task_args["init_args"]
        )
        list_of_images.extend(list_updates["image_list_updates"])
