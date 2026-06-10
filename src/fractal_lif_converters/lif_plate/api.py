"""Python API for LIF Plate converters."""

from ome_zarr_converters_tools import (
    ConverterOptions,
    OverwriteMode,
    RunnerType,
    exec_compound_task,
)
from ome_zarr_converters_tools.fractal import ImageListUpdateDict

from fractal_lif_converters.common.image_in_plate_compute_task import (
    image_in_plate_compute_task,
)
from fractal_lif_converters.lif_plate.convert_lif_plate_init_task import (
    LifPlateAcquisitionModel,
    convert_lif_plate_init_task,
)


def convert_lif_plate(
    *,
    zarr_dir: str,
    acquisitions: list[LifPlateAcquisitionModel],
    converter_options: ConverterOptions | None = None,
    overwrite: OverwriteMode = OverwriteMode.NO_OVERWRITE,
    runner: RunnerType | None = None,
) -> list[ImageListUpdateDict]:
    """Convert a LIF plate dataset to OME-Zarr.

    Args:
        zarr_dir (str): Directory to store the Zarr files.
        acquisitions (list[LifPlateAcquisitionModel]): List of raw acquisitions to
            convert to OME-Zarr.
        converter_options (ConverterOptions | None): Advanced converter options.
        overwrite (OverwriteMode): Overwrite mode for existing data.
        runner (RunnerType | None): Execution strategy for compute tasks.

    Returns:
        list[ImageListUpdateDict]: List of image list update dicts for the converted
            Zarr images.
    """
    converter_options = converter_options or ConverterOptions()
    init_task_kwargs = {
        "zarr_dir": zarr_dir,
        "acquisitions": acquisitions,
        "converter_options": converter_options,
        "overwrite": overwrite,
    }
    return exec_compound_task(
        init_task_fn=convert_lif_plate_init_task,
        compute_task_fn=image_in_plate_compute_task,
        init_task_kwargs=init_task_kwargs,
        runner=runner,
    )
