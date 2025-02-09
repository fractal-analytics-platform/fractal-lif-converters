"""ScanR to OME-Zarr conversion task initialization."""

import logging
from pathlib import Path
from typing import Literal, Optional

from fractal_converters_tools.omezarr_plate_writers import initiate_ome_zarr_plates
from fractal_converters_tools.task_common_models import (
    AdvancedComputeOptions,
)
from fractal_converters_tools.task_init_tools import build_parallelization_list
from pydantic import BaseModel, Field, model_validator, validate_call

from fractal_lif_converters.plate_parser import parse_lif_plate_metadata

logger = logging.getLogger(__name__)


class LifPlateInputModel(BaseModel):
    """Acquisition metadata.

    Attributes:
        path (str): Path to the lif file.
        tile_scan_name (Optional[str]): Optional name of the tile scan.
            If not provided, all tile scans will be considered.
        plate_name (Optional[str]): Optional name of the plate.
            If not provided, the plate name will be inferred from the
            lif file + scan name.
            If the tile scan name is not provided, this field can not be
            used.
        acquisition_id: Acquisition ID, used to identify multiple rounds
            of acquisitions for the same plate.
            If tile_scan_name is not provided, this field can not be used.
    """

    path: str
    tile_scan_name: Optional[str] = None
    plate_name: Optional[str] = None
    acquisition_id: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def check_plate_name(self):
        """Check if the plate name/acquisition is provided correctly."""
        if self.tile_scan_name is not None:
            return self

        if self.plate_name is not None:
            raise ValueError(
                "'plate_name' can only be used when 'tile_scan_name' is provided."
            )

        if self.acquisition_id != 0:
            raise ValueError(
                "'acquisition_id' can only be used when 'tile_scan_name' is provided."
            )

        return self


class AdvancedOptions(AdvancedComputeOptions):
    """Advanced options for the conversion.

    Attributes:
        num_levels (int): The number of resolution levels in the pyramid.
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

    position_scale: Optional[float] = None


@validate_call
def convert_lif_plate_init_task(
    *,
    # Fractal parameters
    zarr_urls: list[str],
    zarr_dir: str,
    # Task parameters
    acquisitions: list[LifPlateInputModel],
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

        _tiled_images = parse_lif_plate_metadata(
            acq_path,
            scan_name=acq.tile_scan_name,
            plate_name=acq.plate_name,
            acquisition_id=acq.acquisition_id,
            scale_m=advanced_options.position_scale,
        )

        if not _tiled_images:
            logger.warning(f"No images found in {acq_path}")
            continue
        tiled_images.extend(list(_tiled_images))

    # Common fractal-converters-tools functions
    parallelization_list = build_parallelization_list(
        zarr_dir=zarr_dir,
        tiled_images=tiled_images,
        overwrite=overwrite,
        advanced_compute_options=advanced_options,
    )
    logger.info(f"Total {len(parallelization_list)} images to convert.")

    initiate_ome_zarr_plates(
        zarr_dir=zarr_dir,
        tiled_images=tiled_images,
        overwrite=overwrite,
    )
    logger.info(f"Initialized OME-Zarr Plate at: {zarr_dir}")
    return {"parallelization_list": parallelization_list}


if __name__ == "__main__":
    from fractal_tasks_core.tasks._utils import run_fractal_task

    run_fractal_task(task_function=convert_lif_plate_init_task, logger_name=logger.name)
