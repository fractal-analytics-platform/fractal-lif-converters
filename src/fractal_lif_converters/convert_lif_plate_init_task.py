"""ScanR to OME-Zarr conversion task initialization."""

import logging
import pickle
from pathlib import Path
from typing import Literal, Optional

from fractal_converters_tools.omezarr_plate_writers import initiate_ome_zarr_plates
from pydantic import BaseModel, Field, validate_call

from fractal_lif_converters.plate_parser import parse_lif_plate_metadata

logger = logging.getLogger(__name__)


class LifPlateInputModel(BaseModel):
    """Acquisition metadata.

    Attributes:
        path: Path to the acquisition directory.
            For scanr, this should include a 'data/' directory with the tiff files
            and a metadata.ome.xml file.
        plate_name: Optional custom name for the plate. If not provided, the name will
            be the acquisition directory name.
        acquisition_id: Acquisition ID,
            used to identify the acquisition in case of multiple acquisitions.
    """

    path: str
    tile_scan_name: Optional[str] = None
    plate_name: Optional[str] = None
    acquisition_id: int = Field(default=0, ge=0)


class AdvancedOptions(BaseModel):
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
        t_chunk (int): T chunk size
    """

    num_levels: int = Field(default=5, ge=1)
    tiling_mode: Literal["auto", "grid", "free", "none"] = "auto"
    swap_xy: bool = False
    invert_x: bool = False
    invert_y: bool = False
    max_xy_chunk: int = Field(default=4096, ge=1)
    z_chunk: int = Field(default=10, ge=1)
    c_chunk: int = Field(default=1, ge=1)
    t_chunk: int = Field(default=1, ge=1)
    position_scale: Optional[float] = None


class ConvertLifInitArgs(BaseModel):
    """Arguments for the compute task."""

    tiled_image_pickled_path: str
    advanced_options: AdvancedOptions = Field(default_factory=AdvancedOptions)


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
    tiled_images, parallelization_list = [], []
    for acq in acquisitions:
        acq_path = Path(acq.path)
        plate_name = acq.plate_name
        scan_name = acq.tile_scan_name

        _tiled_images = parse_lif_plate_metadata(
            acq_path,
            scan_name=scan_name,
            plate_name=plate_name,
            acquisition_id=acq.acquisition_id,
            scale_m=advanced_options.position_scale,
        )

        if not _tiled_images:
            logger.warning(f"No images found in {acq_path}")
            continue

        logger.info(f"Found {len(_tiled_images)} images in {acq_path})")
        for tile_id, tiled_image in _tiled_images.items():
            # pickle the tiled_image
            tile_id_pickle_path = (
                zarr_dir
                / f"_tmp_{tiled_image.path_builder.plate_path}"
                / f"{tile_id}.pickle"
            )
            tile_id_pickle_path.parent.mkdir(parents=True, exist_ok=True)

            with open(tile_id_pickle_path, "wb") as f:
                pickle.dump(tiled_image, f)

            parallelization_list.append(
                {
                    "zarr_url": str(zarr_dir),
                    "init_args": ConvertLifInitArgs(
                        tiled_image_pickled_path=str(tile_id_pickle_path),
                        advanced_options=advanced_options,
                    ).model_dump(),
                }
            )
        tiled_images.extend(list(_tiled_images.values()))

    if not tiled_images:
        raise ValueError("No images found in the acquisitions.")

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
