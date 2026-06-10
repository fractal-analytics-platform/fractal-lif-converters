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
    if current != list(_CANONICAL):
        perm = [current.index(d) for d in _CANONICAL]
        arr = np.transpose(arr, perm)
    # arr is now (T, C, Z, Y, X); squeeze T when T=1
    if arr.shape[0] == 1:
        arr = arr[0]
    return arr


def _load_lif_array(file_path: str, image_id: int, m: int) -> np.ndarray:
    # Re-opening per call is intentional: profiling shows LifFile lifecycle
    # is ~3% of wall time vs ~4% for asarray. Caching handles would also
    # need per-thread state (LifFile is not thread-safe) for marginal gain.
    with liffile.LifFile(file_path, squeeze=False) as lf:
        lif_image = lf.images[image_id]
        dims = list(lif_image.dims)
        if "M" in dims:
            # frames-API output order: iterated dims (original order) +
            # fixed dims + frame dims (Y, X, optional S). M is the only
            # fixed dim here, so its singleton axis sits just before the
            # frame dims.
            arr = lif_image.frames(M=m).asarray()
            frame_dim_count = sum(1 for d in dims if d in ("Y", "X", "S"))
            arr = np.squeeze(arr, axis=arr.ndim - frame_dim_count - 1)
            dims.remove("M")
        else:
            arr = lif_image.asarray()
    return _to_canonical_shape(arr, tuple(dims))


def _peek_lif_dtype(file_path: str, image_id: int, m: int) -> str:
    with liffile.LifFile(file_path, squeeze=False) as lf:
        return str(lf.images[image_id].dtype)


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
