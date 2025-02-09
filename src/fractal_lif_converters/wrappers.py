"""Utility for running the init and compute tasks with a single function call."""

from pathlib import Path

from fractal_lif_converters.convert_lif_compute_task import (
    convert_lif_compute_task,
)
from fractal_lif_converters.convert_lif_plate_init_task import (
    AdvancedOptions,
    LifPlateInputModel,
    convert_lif_plate_init_task,
)
from fractal_lif_converters.convert_lif_single_acq_init_task import (
    LifSingleAcqInputModel,
    convert_lif_single_acq_init_task,
)


def convert_lif_plate_to_omezarr(
    zarr_dir: Path | str,
    acquisitions: list[LifPlateInputModel] | str | Path,
    overwrite: bool = False,
    num_levels: int = 5,
    tiling_mode: str = "auto",
    swap_xy: bool = False,
    invert_x: bool = False,
    invert_y: bool = False,
    max_xy_chunk: int = 4096,
    z_chunk: int = 10,
    c_chunk: int = 1,
    t_chunk: int = 1,
    position_scale: float | None = None,
):
    """Convert LIF files to an OME-Zarr Ngff Plate.

    Args:
        zarr_dir (Path | str): Output path to save the OME-Zarr file.
        acquisitions (list[LifPlateInputModel] | str | Path): List of acquisitions to
        convert. Or the path to a file containing the acquisitions.
        num_levels (int): The number of resolution levels. Defaults to 5.
        overwrite (bool): If True, the zarr store will be overwritten.
        tiling_mode (Literal["auto", "grid", "free", "none"]): Specify the tiling mode.
            "auto" will automatically determine the tiling mode.
            "grid" if the input data is a grid, it will be tiled using snap-to-grid.
            "free" will remove any overlap between tiles using a snap-to-corner
            approach.
            "none" will write the positions as is, using the microscope metadata.
        swap_xy (bool): Swap x and y axes coordinates in the metadata. This is sometimes
            necessary to ensure correct image tiling and registration.
        invert_x (bool): Invert x axis coordinates in the metadata. This is
            sometimes necessary to ensure correct image tiling and registration.
        invert_y (bool): Invert y axis coordinates in the metadata. This is
            sometimes necessary to ensure correct image tiling and registration.
        max_xy_chunk (int): XY chunk size is set as the minimum of this value and the
            microscope tile size.
        z_chunk (int): Z chunk size.
        c_chunk (int): C chunk size.
        t_chunk (int): T chunk size.
        position_scale (Optional[float]): Scale factor for the position coordinates.

    """
    if isinstance(acquisitions, str | Path):
        acquisitions = [LifPlateInputModel(path=acquisitions)]
    parallelization_list = convert_lif_plate_init_task(
        zarr_urls=[],
        zarr_dir=str(zarr_dir),
        acquisitions=acquisitions,
        overwrite=overwrite,
        advanced_options=AdvancedOptions(
            num_levels=num_levels,
            tiling_mode=tiling_mode,
            swap_xy=swap_xy,
            invert_x=invert_x,
            invert_y=invert_y,
            max_xy_chunk=max_xy_chunk,
            z_chunk=z_chunk,
            c_chunk=c_chunk,
            t_chunk=t_chunk,
            position_scale=position_scale,
        ),
    )

    list_of_images = []
    for task_args in parallelization_list["parallelization_list"]:
        list_updates = convert_lif_compute_task(
            zarr_url=task_args["zarr_url"], init_args=task_args["init_args"]
        )
        list_of_images.extend(list_updates["image_list_updates"])


def convert_lif_single_acq_to_omezarr(
    zarr_dir: Path | str,
    acquisitions: list[LifSingleAcqInputModel] | str | Path,
    overwrite: bool = False,
    num_levels: int = 5,
    tiling_mode: str = "auto",
    swap_xy: bool = False,
    invert_x: bool = False,
    invert_y: bool = False,
    max_xy_chunk: int = 4096,
    z_chunk: int = 10,
    c_chunk: int = 1,
    t_chunk: int = 1,
    position_scale: float | None = None,
):
    """Convert LIF files to an OME-Zarr Ngff Plate.

    Args:
        zarr_dir (Path | str): Output path to save the OME-Zarr file.
        acquisitions (list[LifPlateInputModel] | str | Path): List of acquisitions to
        convert. Or the path to a file containing the acquisitions.
        num_levels (int): The number of resolution levels. Defaults to 5.
        overwrite (bool): If True, the zarr store will be overwritten.
        tiling_mode (Literal["auto", "grid", "free", "none"]): Specify the tiling mode.
            "auto" will automatically determine the tiling mode.
            "grid" if the input data is a grid, it will be tiled using snap-to-grid.
            "free" will remove any overlap between tiles using a snap-to-corner
            approach.
            "none" will write the positions as is, using the microscope metadata.
        swap_xy (bool): Swap x and y axes coordinates in the metadata. This is sometimes
            necessary to ensure correct image tiling and registration.
        invert_x (bool): Invert x axis coordinates in the metadata. This is
            sometimes necessary to ensure correct image tiling and registration.
        invert_y (bool): Invert y axis coordinates in the metadata. This is
            sometimes necessary to ensure correct image tiling and registration.
        max_xy_chunk (int): XY chunk size is set as the minimum of this value and the
            microscope tile size.
        z_chunk (int): Z chunk size.
        c_chunk (int): C chunk size.
        t_chunk (int): T chunk size.
        position_scale (Optional[float]): Scale factor for the position coordinates.

    """
    if isinstance(acquisitions, str | Path):
        acquisitions = [LifSingleAcqInputModel(path=acquisitions)]
    parallelization_list = convert_lif_single_acq_init_task(
        zarr_urls=[],
        zarr_dir=str(zarr_dir),
        acquisitions=acquisitions,
        overwrite=overwrite,
        advanced_options=AdvancedOptions(
            num_levels=num_levels,
            tiling_mode=tiling_mode,
            swap_xy=swap_xy,
            invert_x=invert_x,
            invert_y=invert_y,
            max_xy_chunk=max_xy_chunk,
            z_chunk=z_chunk,
            c_chunk=c_chunk,
            t_chunk=t_chunk,
            position_scale=position_scale,
        ),
    )

    list_of_images = []
    for task_args in parallelization_list["parallelization_list"]:
        list_updates = convert_lif_compute_task(
            zarr_url=task_args["zarr_url"], init_args=task_args["init_args"]
        )
        list_of_images.extend(list_updates["image_list_updates"])
