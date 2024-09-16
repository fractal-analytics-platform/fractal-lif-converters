"""Package description."""

from importlib.metadata import PackageNotFoundError, version

from lif_converters.converter_wrapper import lif_plate_converter, lif_scene_converter

try:
    __version__ = version("lif-converters")
except PackageNotFoundError:
    __version__ = "uninstalled"

__all__ = ["lif_plate_converter", "lif_scene_converter"]
