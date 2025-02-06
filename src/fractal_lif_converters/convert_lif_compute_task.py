"""ScanR to OME-Zarr conversion task compute."""

import logging
import pickle
import time
from functools import partial
from pathlib import Path

from fractal_converters_tools.omezarr_image_writers import write_tiled_image
from fractal_converters_tools.stitching import standard_stitching_pipe
from fractal_converters_tools.tiled_image import PlatePathBuilder
from pydantic import validate_call

from fractal_lif_converters.convert_lif_plate_init_task import ConvertLifInitArgs

logger = logging.getLogger(__name__)


@validate_call
def convert_lif_compute_task(
    *,
    # Fractal parameters
    zarr_url: str,
    init_args: ConvertLifInitArgs,
):
    """Initialize the task to convert a LIF plate to OME-Zarr.

    Args:
        zarr_url (str): URL to the OME-Zarr file.
        init_args (ConvertScanrInitArgs): Arguments for the initialization task.
    """
    timer = time.time()
    tiled_image = pickle.load(open(init_args.tiled_image_pickled_path, "rb"))
    logger.info(f"Writing {tiled_image.path}")

    stitching_pipe = partial(
        standard_stitching_pipe,
        mode=init_args.advanced_options.tiling_mode,
        swap_xy=init_args.advanced_options.swap_xy,
        invert_x=init_args.advanced_options.invert_x,
        invert_y=init_args.advanced_options.invert_y,
    )

    new_zarr_url, is_3d, is_time_series = write_tiled_image(
        zarr_dir=zarr_url,
        tiled_image=tiled_image,
        stiching_pipe=stitching_pipe,
        num_levels=init_args.advanced_options.num_levels,
        max_xy_chunk=init_args.advanced_options.max_xy_chunk,
        z_chunk=init_args.advanced_options.z_chunk,
        c_chunk=init_args.advanced_options.c_chunk,
        t_chunk=init_args.advanced_options.t_chunk,
        # Since the init task already checks for overwriting, we can safely pass the
        # overwrite flag here.
        # For future reference, we should consider checking for overwriting here as well.
        # If we allow for partial overwriting.
        overwrite=True,
    )

    p_types = {"is_3D": is_3d}

    if isinstance(tiled_image.path_builder, PlatePathBuilder):
        attributes = {
            "well": f"{tiled_image.path_builder.row}{tiled_image.path_builder.column}",
            "plate": tiled_image.path_builder.plate_path,
        }
    else:
        attributes = {}

    # Clean up the pickled file and the directory if it is empty
    Path(init_args.tiled_image_pickled_path).unlink()
    if not list(Path(init_args.tiled_image_pickled_path).parent.iterdir()):
        Path(init_args.tiled_image_pickled_path).parent.rmdir()
    logger.info(f"convert_scanr_compute_task took {time.time() - timer} seconds")
    return {
        "image_list_updates": [
            {"zarr_url": new_zarr_url, "types": p_types, "attributes": attributes}
        ]
    }


if __name__ == "__main__":
    from fractal_tasks_core.tasks._utils import run_fractal_task

    run_fractal_task(task_function=convert_lif_compute_task, logger_name=logger.name)
