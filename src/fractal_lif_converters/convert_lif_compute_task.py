"""This task converts simple H5 files to OME-Zarr."""

from pathlib import Path

from pydantic import BaseModel, Field, validate_call

from fractal_lif_converters.utils.converter_utils import (
    export_ngff_plate_acquisition,
    export_ngff_single_scene,
)


class ComputeInputModel(BaseModel):
    """Input model for the lif_converter_compute_task."""

    lif_path: str
    scene_name: str
    num_levels: int = Field(5, ge=0)
    coarsening_xy: int = Field(2, ge=1)
    overwrite: bool = False
    plate_mode: bool = True
    swap_xy_axes: bool = False


@validate_call
def convert_lif_compute_task(
    *,
    # Fractal parameters
    zarr_url: str,
    init_args: ComputeInputModel,
):
    """Export a single scene or plate acquisition from a LIF file to OME-Zarr.

    Args:
        zarr_url (str): The path to the zarr store.
        init_args (ComputeInputModel): The input parameters for the conversion.
    """
    zarr_url = Path(zarr_url)
    lif_path = Path(init_args.lif_path)

    func = (
        export_ngff_plate_acquisition
        if init_args.plate_mode
        else export_ngff_single_scene
    )

    new_zarr_url, types, attributes = func(
        zarr_url=zarr_url,
        lif_path=lif_path,
        scene_name=init_args.scene_name,
        num_levels=init_args.num_levels,
        coarsening_xy=init_args.coarsening_xy,
        overwrite=init_args.overwrite,
        swap_xy_axes=init_args.swap_xy_axes,
    )

    return {
        "image_list_updates": [
            {"zarr_url": new_zarr_url, "types": types, "attributes": attributes}
        ]
    }


if __name__ == "__main__":
    from fractal_tasks_core.tasks._utils import run_fractal_task

    run_fractal_task(task_function=convert_lif_compute_task)
