"""This task converts simple H5 files to OME-Zarr."""

from pathlib import Path

import bioio_lif
from bioio import BioImage
from pydantic import validate_call
from src.lif_converters.converter_utils import (
    setup_plate_ome_zarr,
)


@validate_call
def lif_plate_converter_init_task(
    zarr_dir: str,
    lif_files_path: str,
    num_levels=5,
    coarsening_xy=2.0,
    overwrite: bool = False,
):
    """Initialize the conversion of LIF files to OME-Zarr.

    Args:
        zarr_dir (str): Output path to save the OME-Zarr file.
        lif_files_path (str): Input path to the LIF file,
            or a folder containing LIF files.
        num_levels (int): The number of resolution levels. Defaults to 5.
        coarsening_xy (float): The scaling factor for the xy axes. Defaults to 2.0.
        overwrite (bool): If True, the zarr store will be overwritten.
    """
    lif_files_path = Path(lif_files_path)
    zarr_dir = Path(zarr_dir)
    zarr_dir.mkdir(exist_ok=True, parents=True)

    if not lif_files_path.exists():
        raise FileNotFoundError(f"{lif_files_path} does not exist")

    if not lif_files_path.is_dir():
        all_lif_files = list(lif_files_path.glob("*.lif"))
    elif lif_files_path.isfile():
        all_lif_files = [lif_files_path]

    parallelization_list = []

    for lif_path in all_lif_files:
        print(f"Converting {lif_path}")
        img_bio = BioImage(lif_path, reader=bioio_lif.Reader)
        zarr_path = zarr_dir / f"{lif_path.stem}.zarr"
        img_bio = BioImage(lif_path, reader=bioio_lif.Reader)
        zarr_path = zarr_dir / f"{lif_path.stem}.zarr"

        try:
            # TODO create an error for time series
            if img_bio.dims.T > 1:
                raise ValueError("Time series not supported yet")

            setup_plate_ome_zarr(
                zarr_path=zarr_path,
                img_bio=img_bio,
                num_levels=num_levels,
                coarsening_xy=coarsening_xy,
                overwrite=overwrite,
            )

            for scene_name in img_bio.scenes:
                task_kwargs = {
                    "zarr_url": str(zarr_path),
                    "init_args": {
                        "lif_path": str(lif_path),
                        "scene_name": scene_name,
                        "num_levels": num_levels,
                        "coarsening_xy": coarsening_xy,
                        "overwirtte": overwrite,
                    },
                }
                parallelization_list.append(task_kwargs)

        except ValueError:
            # Todo create more specific errors
            print(f"Error in {lif_path}, skipping it")
            continue

    return {"parallelization_list": parallelization_list}


if __name__ == "__main__":
    from fractal_tasks_core.tasks._utils import run_fractal_task

    run_fractal_task(task_function=lif_plate_converter_init_task)
