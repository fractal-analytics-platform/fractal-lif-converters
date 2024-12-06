"""
Converter from the Lif files (Leica Microscope) to OME-Zarr format.
"""

from importlib.metadata import PackageNotFoundError, version

from fractal_lif_converters.wrappers import (
    convert_lif_plate_to_omezarr,
    convert_lif_scene_to_omezarr,
)

try:
    __version__ = version("fractal_lif-converters")
except PackageNotFoundError:
    __version__ = "uninstalled"

__all__ = ["convert_lif_plate_to_omezarr", "convert_lif_scene_to_omezarr"]
