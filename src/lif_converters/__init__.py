"""
Package description.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("lif-converters")
except PackageNotFoundError:
    __version__ = "uninstalled"
