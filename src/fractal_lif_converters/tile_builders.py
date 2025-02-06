"""Utils to build tiled images from lif files."""

from collections.abc import Generator
from enum import Enum
from functools import cache
from typing import Any

import numpy as np
from fractal_converters_tools.tile import Point, Tile, Vector, OriginDict
from fractal_converters_tools.tiled_image import (
    PlatePathBuilder,
    SimplePathBuilder,
    TiledImage,
)
from ngio.ngff_meta.fractal_image_meta import PixelSize
from pydantic import BaseModel
from readlif.reader import LifFile, LifImage
from readlif.utilities import get_xml


class ImageType(Enum):
    """Lif image types.

    single image: Each tile/position is stored as a separate LifImage.
    mosaic image: All tiles/positions are stored in a single LifImage.
    """

    SINGLE = "single"
    MOSAIC = "mosaic"

    @classmethod
    def from_metadata(cls, metadata: dict) -> "ImageType":
        """Get image type from metadata."""
        if "mosaic_position" in metadata and len(metadata["mosaic_position"]) > 0:
            return cls.MOSAIC
        return cls.SINGLE


class ImageInPlateInfo(BaseModel):
    """Utility class to store image information."""

    image_id: int
    image_type: ImageType
    scan_name: str
    row: str
    column: str
    acquisition_id: int

    @property
    def tile_id(self) -> str:
        """Tile Identifier."""
        return f"{self.scan_name}/{self.row}/{self.column}/{self.acquisition_id}"


class ImageInfo(BaseModel):
    """Utility class to store image information."""

    image_id: int
    image_type: ImageType
    scan_name: str

    @property
    def tile_id(self) -> str:
        """Tile Identifier."""
        return f"{self.scan_name}"


class LifTileLoader:
    """Lif tile loader."""

    def __init__(self, path: str, image_id: int, m: int, shape: tuple[int]):
        """Initialize LifTileLoader."""
        self.path = path
        self.image_id = image_id
        self.m = m
        self.shape = shape

    @staticmethod
    def _get_frame(
        lif_image, t: int = 0, c: int = 0, z: int = 0, m: int = 0
    ) -> np.ndarray:
        pil_image = lif_image.get_frame(t=t, c=c, z=z, m=m)
        return np.array(pil_image)

    @property
    def dtype(self):
        """Get the data type of the tile."""
        lif_file = LifFile(self.path)
        lif_image = lif_file.get_image(self.image_id)
        frame = self._get_frame(lif_image=lif_image, m=self.m)
        return frame.dtype

    def load(self) -> np.ndarray:
        """Load the tile data."""
        lif_file = LifFile(self.path)
        lif_image = lif_file.get_image(self.image_id)

        frame = self._get_frame(lif_image=lif_image, m=self.m)
        if frame.ndim != 2:
            raise ValueError("Frame must be 2D.")
        tile_data = np.zeros(shape=self.shape, dtype=frame.dtype)

        for t in range(self.shape[0]):
            for c in range(self.shape[1]):
                for z in range(self.shape[2]):
                    tile_data[t, c, z] = self._get_frame(
                        lif_image=lif_image, t=t, c=c, z=z, m=self.m
                    )
        return tile_data


def build_tiles_mosaic(
    lif_image, image_id, scale_m: float | None = None
) -> Generator[Tile, Any, None]:
    """Build tiles for mosaic images.

    1: "x",
    2: "y",
    3: "z",
    4: "t",
    5: "detection_wavelength",
    6: "unknown",
    7: "unknown",
    9: "illumination_wavelength",
    10: "mosaic_tile",
    """
    shape_x = lif_image.dims_n.get(1, 1)
    shape_y = lif_image.dims_n.get(2, 1)
    shape_t = lif_image.dims_n.get(4, 1)
    shape_z = lif_image.dims_n.get(3, 1)
    shape_c = lif_image.channels

    # scale factors
    # scale_n [px]/[um]
    scale_x = 1 / lif_image.scale_n.get(1, 1)
    scale_y = 1 / lif_image.scale_n.get(2, 1)
    scale_z = 1 / lif_image.scale_n.get(3, 1)
    scale_t = 1  # lif_image.scale_n.get(4, 1)

    if scale_m is None:
        scale_m = lif_image.scale_n.get(10, 1e-6)

    # [um]
    length_x = shape_x * scale_x
    length_y = shape_y * scale_y
    length_z = shape_z * scale_z
    length_t = shape_t * scale_t

    z = float(lif_image.settings.get("ZPosition", 0))
    for m, pos in enumerate(lif_image.mosaic_position):
        x = pos[2] / scale_m
        y = pos[3] / scale_m
        top_l = Point(x=x, y=y, z=0, c=0, t=0)
        diag = Vector(x=length_x, y=length_y, z=length_z, c=shape_c, t=length_t)

        tile_loader = LifTileLoader(
            path=lif_image.filename,
            image_id=image_id,
            m=m,
            shape=(shape_t, shape_c, shape_z, shape_y, shape_x),
        )
        pixel_size = PixelSize(x=scale_x, y=scale_y, z=scale_z)
        origin_dict = OriginDict(
            x_micrometer_original=x,
            y_micrometer_original=y,
            z_micrometer_original=z,
            t_original=0,
        )
        tile = Tile(
            top_l=top_l,
            diag=diag,
            pixel_size=pixel_size,
            data_loader=tile_loader,
            origin=origin_dict,
        )
        yield tile


@cache
def _get_xml(path):
    return get_xml(path)[0]


@cache
def _inner_find_nested_element(xml_elem, name):
    found = None
    # Traverse all descendant nodes with tag 'Element'.
    # Note: current_node.iter('Element') includes current_node itself
    # if its tag is 'Element',
    # so we explicitly skip it.
    for elem in xml_elem.iter("Element"):
        if elem is xml_elem:
            continue
        if elem.attrib.get("Name") == name:
            found = elem
            break  # Found the first matching element at this level; stop searching.
    return found


def _find_nested_element(xml_path, name):
    """Search for a nested <Element> node in an XML tree.

    Given the root of an XML tree and a list of names,
    search for a nested <Element> node for each name in the list.

    For example, with names = ["A", "AA", "ABA"]:
      - Find an <Element> with attribute Name="A".
      - Within that element, find an <Element> with Name="AA".
      - Then, within that element, find an <Element> with Name="ABA".

    If any element in the path is not found, the function returns None.

    :param xml_root: The root element of the XML tree.
    :param names: A list of names to follow.
    :return: The final matching Element node, or None if not found.
    """
    current_node = _get_xml(xml_path)
    names = name.split("/")
    for name in names:
        found = _inner_find_nested_element(current_node, name)
        if found is None:
            return None
        current_node = found
    return current_node


@cache
def _remove_nested_elements(element):
    """Remove all descendant nodes with the tag 'Element' from the given element."""
    for child in list(element):
        if child.tag == "Element":
            element.remove(child)
        else:
            _remove_nested_elements(child)
    return element


def find_tile_infos(path: str, name: str):
    """Find the tile information for a given tile name."""
    element = _find_nested_element(path, name)
    if element is None:
        raise ValueError(f"Could not find the postion metadata for {name}")
    element = _remove_nested_elements(element)
    flipx, flipy, swap_xy = False, False, False
    tiles = []
    for child in element.iter():
        if child.tag == "Tile":
            tiles.append(dict(child.attrib))
        if child.tag == "Attachment" and "FlipX" in child.attrib:
            flipx = True if child.attrib["FlipX"] == "1" else False
        if child.tag == "Attachment" and "FlipY" in child.attrib:
            flipy = True if child.attrib["FlipY"] == "1" else False
        if child.tag == "Attachment" and "SwapXY" in child.attrib:
            swap_xy = True if child.attrib["SwapXY"] == "1" else False

    if len(tiles) == 0:
        raise ValueError(f"Could not find the postion metadata for {name}")

    if len(tiles) > 1:
        raise ValueError(
            f"Found multiple tiles position for {name}. "
            "But the image is not a mosaic. This case is not supported."
        )
    return tiles[0], flipx, flipy, swap_xy


def build_single_tile(lif_image, image_id):
    """Build a tile for single images."""
    shape_x = lif_image.dims_n.get(1, 1)
    shape_y = lif_image.dims_n.get(2, 1)
    shape_t = lif_image.dims_n.get(4, 1)
    shape_z = lif_image.dims_n.get(3, 1)
    shape_c = lif_image.channels

    # scale factors
    # scale_n [px]/[um]
    scale_x = 1 / lif_image.scale_n.get(1, 1)
    scale_y = 1 / lif_image.scale_n.get(2, 1)
    scale_z = 1 / lif_image.scale_n.get(3, 1)
    scale_t = 1  # lif_image.scale_n.get(4, 1)
    scale_m = lif_image.scale_n.get(10, 1e-6)

    length_x = shape_x * scale_x
    length_y = shape_y * scale_y
    length_z = shape_z * scale_z
    length_t = shape_t * scale_t

    tile_info, _, _, _ = find_tile_infos(lif_image.filename, lif_image.name)
    x = float(tile_info.get("PosX", 0))
    y = float(tile_info.get("PosY", 0))
    z = float(lif_image.settings.get("ZPosition", 0))

    x = x / scale_m
    y = y / scale_m
    z = z / scale_m

    top_l = Point(x=x, y=y, z=0, c=0, t=0)
    diag = Vector(x=length_x, y=length_y, z=length_z, c=shape_c, t=length_t)
    tile_loader = LifTileLoader(
        path=lif_image.filename,
        image_id=image_id,
        m=0,
        shape=(shape_t, shape_c, shape_z, shape_y, shape_x),
    )
    pixel_size = PixelSize(x=scale_x, y=scale_y, z=scale_z)

    origin_dict = OriginDict(
        x_micrometer_original=x,
        y_micrometer_original=y,
        z_micrometer_original=z,
        t_original=0,
    )
    tile = Tile(
        top_l=top_l,
        diag=diag,
        pixel_size=pixel_size,
        data_loader=tile_loader,
        origin=origin_dict,
    )
    return tile


def collect_plate_acq_mosaic(
    lif_file: LifFile,
    image_infos: list[ImageInPlateInfo],
    plate_name: str,
    channel_names: list[str] | None,
    channel_wavelengths,
    num_levels,
    scale_m: float | None = None,
) -> dict[str, TiledImage]:
    """Collect tiled images for mosaic acquisitions."""
    if len(image_infos) != 1:
        raise ValueError(
            "Only one mosaic image is expected. Multi-mosaic is not supported."
        )
    image_info = image_infos[0]
    path_builder = PlatePathBuilder(
        plate_name=plate_name,
        row=image_info.row,
        column=int(image_info.column),
        acquisition_id=image_info.acquisition_id,
    )
    lif_image = lif_file.get_image(image_info.image_id)
    tiled_image = TiledImage(
        name=lif_image.filename,
        path_builder=path_builder,
        channel_names=channel_names,
        wavelength_ids=channel_wavelengths,
        num_levels=num_levels,
    )
    for tile in build_tiles_mosaic(lif_image, image_info.image_id, scale_m):
        tiled_image.add_tile(tile)

    return tiled_image


def collect_plate_acq_single(
    lif_file: LifFile,
    image_infos: list[ImageInPlateInfo],
    plate_name: str,
    channel_names: list[str] | None,
    channel_wavelengths,
    num_levels,
) -> dict[str, TiledImage]:
    """Collect tiled images for single acquisitions."""
    if len(image_infos) == 0:
        raise ValueError("No images found for the given tile id.")

    image_info = image_infos[0]
    path_builder = PlatePathBuilder(
        plate_name=plate_name,
        row=image_info.row,
        column=int(image_info.column),
        acquisition_id=image_info.acquisition_id,
    )
    lif_image = lif_file.get_image(image_info.image_id)
    tiled_image = TiledImage(
        name=lif_image.filename,
        path_builder=path_builder,
        channel_names=channel_names,
        wavelength_ids=channel_wavelengths,
        num_levels=num_levels,
    )
    for info in image_infos:
        lif_image = lif_file.get_image(info.image_id)
        tile = build_single_tile(lif_image, info.image_id)
        tiled_image.add_tile(tile)

    return tiled_image


def collect_single_acq_mosaic(
    lif_image: LifImage,
    image_info: ImageInfo,
    zarr_name: str,
    channel_names: list[str] | None,
    channel_wavelengths,
    num_levels,
    scale_m: float | None = None,
) -> dict[str, TiledImage]:
    """Collect tiled images for single mosaic acquisitions."""
    path_builder = SimplePathBuilder(
        path=zarr_name,
    )
    tiled_image = TiledImage(
        name=lif_image.filename,
        path_builder=path_builder,
        channel_names=channel_names,
        wavelength_ids=channel_wavelengths,
        num_levels=num_levels,
    )
    for tile in build_tiles_mosaic(lif_image, image_info.image_id, scale_m):
        tiled_image.add_tile(tile)

    return tiled_image


def collect_single_acq_single(
    lif_image: LifImage,
    image_info: ImageInfo,
    zarr_name: str,
    channel_names: list[str] | None,
    channel_wavelengths,
    num_levels,
) -> dict[str, TiledImage]:
    raise NotImplementedError
