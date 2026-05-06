"""LIF single-acquisition init task."""

# Import for side effect: registers the SingleImage collection setup handler
# with ome_zarr_converters_tools.
from fractal_lif_converters.lif_single import _setup  # noqa: F401
from fractal_lif_converters.lif_single.convert_lif_single_acq_init_task import (
    LifSingleAcqAcquisitionModel,
    convert_lif_single_acq_init_task,
)

__all__ = [
    "LifSingleAcqAcquisitionModel",
    "convert_lif_single_acq_init_task",
]
