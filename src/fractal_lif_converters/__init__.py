"""Converter from the Lif files (Leica Microscope) to OME-Zarr format."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("fractal_lif_converters")
except PackageNotFoundError:
    __version__ = "uninstalled"

from fractal_lif_converters.lif_image import LifImageAcquisitionModel, convert_lif_image
from fractal_lif_converters.lif_plate import LifPlateAcquisitionModel, convert_lif_plate

__all__ = [
    "LifImageAcquisitionModel",
    "LifPlateAcquisitionModel",
    "__version__",
    "convert_lif_image",
    "convert_lif_plate",
]
