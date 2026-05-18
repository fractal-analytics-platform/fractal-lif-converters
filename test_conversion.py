# This is a test script to convert LIF plate acquisitions to Zarr format using
# the fractal_lif_converters library.
from fractal_lif_converters.common.image_in_plate_compute_task import (
    image_in_plate_compute_task,
)
from fractal_lif_converters.lif_plate.convert_lif_plate_init_task import (
    ConverterOptions,
    LifPlateAcquisitionModel,
    OverwriteMode,
    convert_lif_plate_init_task,
    default_converter_options,
)


def convert_lif_to_zarr(
    zarr_dir: str,
    acquisitions: list[LifPlateAcquisitionModel],
    converter_options: ConverterOptions = default_converter_options,
    overwrite: OverwriteMode = OverwriteMode.NO_OVERWRITE,
):
    """Convert LIF plate acquisitions to Zarr format."""
    result = convert_lif_plate_init_task(
        zarr_dir=zarr_dir,
        acquisitions=acquisitions,
        converter_options=converter_options,
        overwrite=overwrite,
    )
    for item in result["parallelization_list"]:
        image_in_plate_compute_task(**item)


path = "/Users/locerr/data/ZMB_converters/testData_Leica/241203_Stellaris/2w_4f_1t_3c_1z_customPositions_L_512x512.lif"
zarr_dir = "/Users/locerr/Projects/fractal-lif-converters/output/"

convert_lif_to_zarr(
    zarr_dir=zarr_dir,
    acquisitions=[LifPlateAcquisitionModel(path=path)],
    converter_options=ConverterOptions(tiling_mode="Inplace"),
    overwrite=OverwriteMode.OVERWRITE,
)
