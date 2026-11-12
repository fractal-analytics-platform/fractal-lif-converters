"""Initialize the LIF image to OME-Zarr conversion task."""

import logging

from ome_zarr_converters_tools import (
    ConverterOptions,
    OverwriteMode,
    StagePositionCorrections,
    setup_images_for_conversion,
)
from pydantic import Field, model_validator, validate_call

from fractal_lif_converters.common import (
    BaseAcquisitionModel,
    parse_acquisitions,
)
from fractal_lif_converters.common._options import LifAcquisitionOptions
from fractal_lif_converters.lif_image._parser import parse_lif_image_metadata

logger = logging.getLogger("convert_lif_image_task")


# LIF tiles are multi-channel (length_c == number of channels), so the v1 default
# `reindex_channels=True` — which assumes one channel per tile — is incompatible and
# would raise at compute time. Disable it: LIF channel indices are already dense.
default_converter_options = ConverterOptions(
    stage_position_corrections=StagePositionCorrections(reindex_channels=False)
)


class LifImageAcquisitionModel(BaseAcquisitionModel):
    """Acquisition input model for LIF image conversion.

    ``tile_scan_name`` controls whether a single scan is converted (named mode)
    or every scan in the file is processed (wildcard mode).

    ``plate_name`` and ``acquisition_id`` are inherited from
    ``BaseAcquisitionModel`` but have no meaning for ``SingleImage`` outputs.
    """

    tile_scan_name: str | None = None
    """
    Optional name of the tile scan. If ``None``, all scans in the LIF file are
    processed (wildcard mode).
    """
    zarr_name: str | None = None
    """
    Optional zarr name. ``None`` derives the name as ``{lif_stem}_{scan_name}``.
    Cannot be used in wildcard mode (when ``tile_scan_name`` is None).
    """
    advanced: LifAcquisitionOptions = Field(default_factory=LifAcquisitionOptions)
    """Advanced acquisition options (LIF-specific)."""

    @model_validator(mode="after")
    def _check_combo(self) -> "LifImageAcquisitionModel":
        if self.tile_scan_name is None and self.zarr_name is not None:
            raise ValueError(
                "'zarr_name' can only be used when 'tile_scan_name' is provided."
            )
        return self


@validate_call
def convert_lif_image_init_task(
    *,
    # Fractal parameters
    zarr_dir: str,
    # Task parameters
    acquisitions: list[LifImageAcquisitionModel],
    converter_options: ConverterOptions = default_converter_options,
    overwrite: OverwriteMode = OverwriteMode.NO_OVERWRITE,
):
    """Initialize the task to convert a LIF image dataset to OME-Zarr.

    Args:
        zarr_dir (str): Directory to store the Zarr files.
        acquisitions (list[LifImageAcquisitionModel]): List of raw acquisitions
            to convert to OME-Zarr.
        converter_options (ConverterOptions): Advanced converter options.
        overwrite (OverwriteMode): Overwrite mode for existing data.
    """
    tiled_images = parse_acquisitions(
        parse_function=parse_lif_image_metadata,
        acquisitions=acquisitions,
        converter_options=converter_options,
    )

    parallelization_list = setup_images_for_conversion(
        tiled_images=tiled_images,
        zarr_dir=zarr_dir,
        converter_options=converter_options,
        collection_type="SingleImage",
        overwrite_mode=overwrite,
        ngff_version=converter_options.omezarr_options.ngff_version,
    )
    logger.info(
        f"Prepared parallelization list with {len(parallelization_list)} items."
    )
    return {"parallelization_list": parallelization_list}


if __name__ == "__main__":
    from fractal_task_tools.task_wrapper import run_fractal_task

    run_fractal_task(task_function=convert_lif_image_init_task, logger_name=logger.name)
