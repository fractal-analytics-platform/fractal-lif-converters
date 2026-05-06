"""Initialize the LIF Plate to OME-Zarr conversion task."""

import logging
from pathlib import Path

from ome_zarr_converters_tools import (
    ConverterOptions,
    OverwriteMode,
    setup_images_for_conversion,
)
from pydantic import Field, model_validator, validate_call

from fractal_lif_converters.common import (
    BaseAcquisitionModel,
    parse_acquisitions,
)
from fractal_lif_converters.common.options import LifAcquisitionOptions
from fractal_lif_converters.lif_plate.parser import parse_lif_plate_metadata

logger = logging.getLogger("convert_lif_plate_task")


default_converter_options = ConverterOptions()


class LifPlateAcquisitionModel(BaseAcquisitionModel):
    """Acquisition input model for LIF plate conversion.

    ``tile_scan_name`` controls whether a single tile scan is converted
    (named mode) or every plate-shaped tile scan in the file (wildcard mode).
    """

    tile_scan_name: str | None = None
    """
    Optional name of the tile scan. If ``None``, all plate-shaped tile scans
    in the LIF file are processed (wildcard mode).
    """
    advanced: LifAcquisitionOptions = Field(default_factory=LifAcquisitionOptions)
    """Advanced acquisition options (LIF-specific)."""

    @model_validator(mode="after")
    def _check_combo(self) -> "LifPlateAcquisitionModel":
        if self.tile_scan_name is None:
            if self.plate_name is not None:
                raise ValueError(
                    "'plate_name' can only be used when 'tile_scan_name' is provided."
                )
            if self.acquisition_id != 0:
                raise ValueError(
                    "'acquisition_id' can only be used when 'tile_scan_name' is "
                    "provided."
                )
        return self

    @property
    def normalized_plate_name(self) -> str:
        """Return the explicit plate name, falling back to the LIF file stem.

        In wildcard mode the per-scan name is applied at parse time to each
        ``ImageInPlate.plate_name``; this property is only consulted when
        ``plate_name`` is set explicitly.
        """
        if self.plate_name is not None:
            return self.plate_name
        return Path(self.path).stem


@validate_call
def convert_lif_plate_init_task(
    *,
    # Fractal parameters
    zarr_dir: str,
    # Task parameters
    acquisitions: list[LifPlateAcquisitionModel],
    converter_options: ConverterOptions = default_converter_options,
    overwrite: OverwriteMode = OverwriteMode.NO_OVERWRITE,
):
    """Initialize the task to convert a LIF plate dataset to OME-Zarr.

    Args:
        zarr_dir (str): Directory to store the Zarr files.
        acquisitions (list[LifPlateAcquisitionModel]): List of raw acquisitions to
            convert to OME-Zarr.
        converter_options (ConverterOptions): Advanced converter options.
        overwrite (OverwriteMode): Overwrite mode for existing data.
    """
    tiled_images = parse_acquisitions(
        parse_function=parse_lif_plate_metadata,
        acquisitions=acquisitions,
        converter_options=converter_options,
    )

    parallelization_list = setup_images_for_conversion(
        tiled_images=tiled_images,
        zarr_dir=zarr_dir,
        converter_options=converter_options,
        collection_type="ImageInPlate",
        overwrite_mode=overwrite,
        ngff_version=converter_options.omezarr_options.ngff_version,
    )
    logger.info(
        f"Prepared parallelization list with {len(parallelization_list)} items."
    )
    return {"parallelization_list": parallelization_list}


if __name__ == "__main__":
    from fractal_task_tools.task_wrapper import run_fractal_task

    run_fractal_task(task_function=convert_lif_plate_init_task, logger_name=logger.name)
