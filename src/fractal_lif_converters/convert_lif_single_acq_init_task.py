"""ScanR to OME-Zarr conversion task initialization."""

import logging
from pathlib import Path
from typing import Optional

from fractal_converters_tools.task_init_tools import build_parallelization_list
from pydantic import BaseModel, model_validator, validate_call

from fractal_lif_converters.convert_lif_plate_init_task import (
    AdvancedOptions,
)
from fractal_lif_converters.single_acq_parser import parse_lif_metadata

logger = logging.getLogger(__name__)


class LifSingleAcqInputModel(BaseModel):
    """Acquisition metadata.

    Attributes:
        path (str): Path to the lif file.
        tile_scan_name (Optional[str]): Optional name of the tile scan.
            If not provided, all tile scans will be considered.
        zarr_name (Optional[str]): Optional name of the Zarr file.
            If not provided, the name will be generated from the
            lif file name + tile scan name.
            If the tile scan name is not provided, theis field can not be
            used.
    """

    path: str
    tile_scan_name: Optional[str] = None
    zarr_name: Optional[str] = None

    @model_validator(mode="after")
    def check_plate_name(self):
        """Check if the plate name/acquisition is provided correctly."""
        if self.tile_scan_name is not None:
            return self

        if self.zarr_name is not None:
            raise ValueError(
                "'zarr_name' can only be used when 'tile_scan_name' is provided."
            )

        return self


@validate_call
def convert_lif_single_acq_init_task(
    *,
    # Fractal parameters
    zarr_urls: list[str],
    zarr_dir: str,
    # Task parameters
    acquisitions: list[LifSingleAcqInputModel],
    overwrite: bool = False,
    advanced_options: AdvancedOptions = AdvancedOptions(),  # noqa: B008
):
    """Initialize the LIF Plate to OME-Zarr conversion task.

    Args:
        zarr_urls (list[str]): List of Zarr URLs.
        zarr_dir (str): Directory to store the Zarr files.
        acquisitions (list[AcquisitionInputModel]): List of raw acquisitions to convert
            to OME-Zarr.
        overwrite (bool): Overwrite existing Zarr files.
        advanced_options (AdvancedOptions): Advanced options for the conversion.
    """
    if not acquisitions:
        raise ValueError("No acquisitions provided.")

    zarr_dir = Path(zarr_dir)

    if not zarr_dir.exists():
        logger.info(f"Creating directory: {zarr_dir}")
        zarr_dir.mkdir(parents=True)

    # prepare the parallel list of zarr urls
    tiled_images = []
    for acq in acquisitions:
        acq_path = Path(acq.path)
        if not acq_path.exists():
            raise FileNotFoundError(f"File not found: {acq_path}")

        _tiled_images = parse_lif_metadata(
            acq_path,
            scan_name=acq.tile_scan_name,
            zarr_name=acq.zarr_name,
            scale_m=advanced_options.position_scale,
        )

        if not _tiled_images:
            logger.warning(f"No images found in {acq_path}")
            continue

        tiled_images.extend(_tiled_images)

    # Common fractal-converters-tools functions
    parallelization_list = build_parallelization_list(
        zarr_dir=zarr_dir,
        tiled_images=tiled_images,
        overwrite=overwrite,
        advanced_compute_options=advanced_options,
    )

    logger.info(f"Total {len(parallelization_list)} images to convert.")
    return {"parallelization_list": parallelization_list}


if __name__ == "__main__":
    from fractal_tasks_core.tasks._utils import run_fractal_task

    run_fractal_task(
        task_function=convert_lif_single_acq_init_task, logger_name=logger.name
    )
