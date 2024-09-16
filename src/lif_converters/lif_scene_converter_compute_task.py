"""This task converts simple H5 files to OME-Zarr."""

from pathlib import Path

from pydantic import validate_call

from lif_converters.utils.converter_utils import export_plate_acquisition_to_zarr


@validate_call
def lif_scene_converter_compute_task(
    zarr_url: str,
    lif_path: str,
    scene_name: str,
    num_levels: int,
    coarsening_xy: float,
    overwrite: bool,
):
    """TODO

    Args:
        zarr_url (str): The path to the zarr store.
        lif_path (str): The path to the LIF file.
        scene_name (str): The name of the scene to convert.
        num_levels (int): The number of resolution levels.
        coarsening_xy (float): The scaling factor for the xy axes.
        overwrite (bool): If True, the zarr store will be overwritten.
    """
    pass


if __name__ == "__main__":
    from fractal_tasks_core.tasks._utils import run_fractal_task

    run_fractal_task(task_function=lif_scene_converter_compute_task)
