"""This task converts simple H5 files to OME-Zarr."""

from pathlib import Path

from pydantic import BaseModel, Field, validate_call

from lif_converters.utils.converter_utils import (
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


# Convert Lif Plate to OME-Zarr
@validate_call
def lif_converter_compute_task(
    *,
    # Fractal parameters
    zarr_url: str,
    init_args: ComputeInputModel,
):
    """Convert a single acquisition (well) in inside an OME-Zarr plate.

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
    )

    return {
        "image_list_updates": [
            {"zarr_url": new_zarr_url, "types": types, "attributes": attributes}
        ]
    }


if __name__ == "__main__":
    from fractal_tasks_core.tasks._utils import run_fractal_task

    run_fractal_task(task_function=lif_converter_compute_task)
