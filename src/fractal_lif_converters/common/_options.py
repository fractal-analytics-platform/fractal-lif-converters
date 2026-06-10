"""LIF-specific acquisition options."""

from ome_zarr_converters_tools import AcquisitionOptions
from pydantic import Field


class LifAcquisitionOptions(AcquisitionOptions):
    """Acquisition options specific to LIF conversion."""

    position_scale: float | None = Field(default=None, title="Position Scale")
    """
    Scale factor (m/px) overriding ``lif_image.scale_n[10]``. Set when stage
    coordinates need a non-default unit conversion.
    """
