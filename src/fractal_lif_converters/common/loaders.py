"""LIF image loaders implementing the ImageLoaderInterface."""

from typing import Any

import liffile
import numpy as np
from ome_zarr_converters_tools.models._loader import ImageLoaderInterface

# Canonical dimension order produced by this loader (excluding T which is
# squeezed when T=1, or kept first when T>1).
_CANONICAL = ("T", "C", "Z", "Y", "X")


def _to_canonical_shape(arr: np.ndarray, dims: tuple) -> np.ndarray:
    """Reshape arr from liffile native dims to (T?,C,Z,Y,X), squeezing T if 1."""
    current = list(dims)
    for i, dim in enumerate(_CANONICAL):
        if dim not in current:
            arr = np.expand_dims(arr, axis=i)
            current.insert(i, dim)
    # arr is now (T, C, Z, Y, X); squeeze T when T=1
    if arr.shape[0] == 1:
        arr = arr[0]
    return arr


def _load_lif_array(file_path: str, image_id: int, m: int) -> np.ndarray:
    with liffile.LifFile(file_path, squeeze=False) as lf:
        lif_image = lf.images[image_id]
        arr = lif_image.asarray()
        dims = list(lif_image.dims)
        if "M" in dims:
            arr = np.take(arr, m, axis=dims.index("M"))
            dims.remove("M")
    return _to_canonical_shape(arr, tuple(dims))


def _peek_lif_dtype(file_path: str, image_id: int, m: int) -> str:
    with liffile.LifFile(file_path, squeeze=False) as lf:
        return str(lf.images[image_id].asarray().dtype)


class LifMosaicLoader(ImageLoaderInterface):
    """Loader for a single mosaic position within a LIF image."""

    file_path: str
    image_id: int
    m: int

    def load_data(self, resource: Any = None) -> np.ndarray:
        """Load the mosaic-position image data as a NumPy array."""
        return _load_lif_array(self.file_path, self.image_id, self.m)

    def find_data_type(self, resource: Any = None) -> str:
        """Find the dtype of the image data without loading the full stack."""
        return _peek_lif_dtype(self.file_path, self.image_id, self.m)
