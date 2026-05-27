"""Converter from the Lif files (Leica Microscope) to OME-Zarr format."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("fractal_lif_converters")
except PackageNotFoundError:
    __version__ = "uninstalled"

__all__ = ["__version__"]
