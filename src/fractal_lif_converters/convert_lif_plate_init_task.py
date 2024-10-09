"""This task converts simple H5 files to OME-Zarr."""

from pathlib import Path

import bioio_lif
from bioio import BioImage
from fractal_tasks_core.utils import logger
from pydantic import Field, validate_call

from fractal_lif_converters.convert_lif_compute_task import ComputeInputModel
from fractal_lif_converters.utils import (
    LifFormatNotSupported,
    TimeSeriesNotSupported,
    setup_plate_ome_zarr,
)


@validate_call
def convert_lif_plate_init_task(
    *,
    # Fractal parameters
    zarr_urls: list[str],
    zarr_dir: str,
    # Task parameters
    lif_files_path: str,
    swap_xy_axes: bool = False,
    num_levels: int = Field(default=5, ge=0),
    coarsening_xy: int = Field(default=2, ge=1),
    overwrite: bool = False,
):
    """Initialize the conversion of LIF files to an OME-Zarr - Plate.

    Args:
        zarr_urls (list[str]): List of zarr urls.
        zarr_dir (str): Output path to save the OME-Zarr file.
        lif_files_path (str): Input path to the LIF file,
            or a folder containing LIF files.
        swap_xy_axes (bool): If True, the xy axes will be swapped. Defaults to False.
        num_levels (int): The number of resolution levels. Defaults to 5.
        coarsening_xy (float): The scaling factor for the xy axes. Defaults to 2.0.
        overwrite (bool): If True, the zarr store will be overwritten.
    """
    lif_files_path = Path(lif_files_path)
    zarr_dir = Path(zarr_dir)
    zarr_dir.mkdir(exist_ok=True, parents=True)

    if not lif_files_path.exists():
        raise FileNotFoundError(f"{lif_files_path} does not exist")

    if lif_files_path.is_dir():
        all_lif_files = list(lif_files_path.glob("*.lif"))
    elif lif_files_path.is_file():
        all_lif_files = [lif_files_path]
    else:
        raise ValueError(f"{lif_files_path} is not a file or a folder")

    parallelization_list = []

    for lif_path in all_lif_files:
        img_bio = BioImage(lif_path, reader=bioio_lif.Reader)
        zarr_path = zarr_dir / f"{lif_path.stem}.zarr"
        img_bio = BioImage(lif_path, reader=bioio_lif.Reader)
        zarr_path = zarr_dir / f"{lif_path.stem}.zarr"

        try:
            # TODO create an error for time series
            if img_bio.dims.T > 1:
                raise TimeSeriesNotSupported("Time dimension greater than 1")

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
                    "init_args": ComputeInputModel(
                        lif_path=str(lif_path),
                        scene_name=scene_name,
                        num_levels=num_levels,
                        coarsening_xy=coarsening_xy,
                        overwrite=overwrite,
                        plate_mode=True,
                        swap_xy_axes=swap_xy_axes,
                    ).model_dump(),
                }
                parallelization_list.append(task_kwargs)
                logger.info(
                    f"{lif_path} - {scene_name} added to the parallelization list."
                )

        except TimeSeriesNotSupported as e:
            logger.warning(f"skipping {lif_path}: {e}")
            continue

        except LifFormatNotSupported as e:
            logger.warning(f"skipping {lif_path}: {e}")

    logger.info(f"Found {len(parallelization_list)} scenes to convert.")
    return {"parallelization_list": parallelization_list}


if __name__ == "__main__":
    from fractal_tasks_core.tasks._utils import run_fractal_task

    run_fractal_task(task_function=convert_lif_plate_init_task)
