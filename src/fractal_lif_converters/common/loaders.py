"""LIF image loaders implementing the ImageLoaderInterface."""

from typing import Any

import numpy as np
from ome_zarr_converters_tools.models._loader import ImageLoaderInterface
from readlif.reader import LifFile


def _load_lif_array(file_path: str, image_id: int, m: int) -> np.ndarray:
    lif_image = LifFile(file_path).get_image(image_id)
    shape_x = lif_image.dims_n.get(1, 1)
    shape_y = lif_image.dims_n.get(2, 1)
    shape_z = lif_image.dims_n.get(3, 1)
    shape_t = lif_image.dims_n.get(4, 1)
    shape_c = lif_image.channels

    first = np.array(lif_image.get_frame(t=0, c=0, z=0, m=m))
    data = np.zeros(
        shape=(shape_t, shape_c, shape_z, shape_y, shape_x), dtype=first.dtype
    )
    for t in range(shape_t):
        for c in range(shape_c):
            for z in range(shape_z):
                data[t, c, z] = np.array(lif_image.get_frame(t=t, c=c, z=z, m=m))

    if shape_t == 1:
        return data[0]
    return data


def _peek_lif_dtype(file_path: str, image_id: int, m: int) -> str:
    lif_image = LifFile(file_path).get_image(image_id)
    frame = np.array(lif_image.get_frame(t=0, c=0, z=0, m=m))
    return str(frame.dtype)


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


