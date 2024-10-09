"""Utility for running the init and compute tasks with a single function call."""

from pathlib import Path

from fractal_lif_converters.convert_lif_compute_task import (
    convert_lif_compute_task,
)
from fractal_lif_converters.convert_lif_plate_init_task import (
    convert_lif_plate_init_task,
)
from fractal_lif_converters.convert_lif_scene_init_task import (
    convert_lif_scene_init_task,
)


def convert_lif_plate_to_omezarr(
    zarr_dir: Path | str,
    lif_files_path: Path | str,
    swap_xy_axes: bool = False,
    num_levels: int = 5,
    coarsening_xy: int = 2,
    overwrite: bool = False,
):
    """Convert LIF files to an OME-Zarr Ngff Plate.

    Args:
        zarr_dir (Path | str): Output path to save the OME-Zarr file.
        lif_files_path (Path | str): Input path to the LIF file,
            or a folder containing LIF files.
        swap_xy_axes (bool): If True, the xy axes will be swapped. Defaults to False.
        num_levels (int): The number of resolution levels. Defaults to 5.
        coarsening_xy (float): The scaling factor for the xy axes. Defaults to 2.0.
        overwrite (bool): If True, the zarr store will be overwritten

    """
    parallelization_list = convert_lif_plate_init_task(
        zarr_urls=[],
        zarr_dir=str(zarr_dir),
        lif_files_path=str(lif_files_path),
        num_levels=num_levels,
        coarsening_xy=coarsening_xy,
        swap_xy_axes=swap_xy_axes,
        overwrite=overwrite,
    )

    list_of_images = []
    for task_args in parallelization_list["parallelization_list"]:
        list_updates = convert_lif_compute_task(
            zarr_url=task_args["zarr_url"], init_args=task_args["init_args"]
        )
        list_of_images.extend(list_updates["image_list_updates"])


def convert_lif_scene_to_omezarr(
    zarr_dir: Path | str,
    lif_files_path: Path | str,
    scene_name: str | None = None,
    swap_xy_axes: bool = False,
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
        swap_xy_axes (bool): If True, the xy axes will be swapped. Defaults to False.
        num_levels (int): The number of resolution levels. Defaults to 5.
        coarsening_xy (float): The scaling factor for the xy axes. Defaults to 2.0.
        overwrite (bool): If True, the zarr store will be overwritten

    """
    parallelization_list = convert_lif_scene_init_task(
        zarr_urls=[],
        zarr_dir=str(zarr_dir),
        lif_files_path=str(lif_files_path),
        scene_name=scene_name,
        num_levels=num_levels,
        coarsening_xy=coarsening_xy,
        swap_xy_axes=swap_xy_axes,
        overwrite=overwrite,
    )

    list_of_images = []
    for task_args in parallelization_list["parallelization_list"]:
        list_updates = convert_lif_compute_task(
            zarr_url=task_args["zarr_url"], init_args=task_args["init_args"]
        )
        list_of_images.extend(list_updates["image_list_updates"])
