"""This task converts simple H5 files to OME-Zarr."""

from pathlib import Path

from pydantic import validate_call

from lif_converters.utils.converter_utils import (
    export_ngff_plate_acquisition,
    export_ngff_single_scene,
)


@validate_call
def lif_converter_compute_task(
    *,
    # Fractal parameters
    zarr_url: str,
    # Task parameters
    lif_path: str,
    scene_name: str,
    num_levels: int,
    coarsening_xy: float,
    overwrite: bool,
    plate_mode: bool = True,
):
    """Convert a single acquisition (well) in inside an OME-Zarr plate.

    Args:
        zarr_url (str): The path to the zarr store.
        lif_path (str): The path to the LIF file.
        scene_name (str): The name of the scene to convert.
        num_levels (int): The number of resolution levels.
        coarsening_xy (float): The scaling factor for the xy axes.
        overwrite (bool): If True, the zarr store will be overwritten.
        plate_mode (bool): If True, the task will convert a plate, otherwise a scene.
    """
    zarr_url = Path(zarr_url)
    lif_path = Path(lif_path)

    func = export_ngff_plate_acquisition if plate_mode else export_ngff_single_scene

    new_zarr_url, types, attributes = func(
        zarr_url=zarr_url,
        lif_path=lif_path,
        scene_name=scene_name,
        num_levels=num_levels,
        coarsening_xy=coarsening_xy,
        overwrite=overwrite,
    )

    return {
        "image_list_updates": [
            {"zarr_url": new_zarr_url, "types": types, "attributes": attributes}
        ]
    }


if __name__ == "__main__":
    from fractal_tasks_core.tasks._utils import run_fractal_task

    run_fractal_task(task_function=lif_converter_compute_task)
