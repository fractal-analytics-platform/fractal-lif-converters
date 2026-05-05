"""Build LIF tiles for the ome-zarr-converters-tools pipeline.

Produces flat ``list[Tile]`` per acquisition; downstream
``tiles_aggregation_pipeline`` is responsible for grouping into ``TiledImage``.
"""

from collections.abc import Callable
from enum import Enum
from functools import cache
from typing import Any

from ome_zarr_converters_tools import (
    AcquisitionDetails,
    ImageInPlate,
    SingleImage,
    Tile,
)
from pydantic import BaseModel
from readlif.reader import LifFile
from readlif.utilities import get_xml

from fractal_lif_converters.lif.loaders import LifMosaicLoader, LifSingleLoader


class ImageType(Enum):
    """LIF image storage types.

    SINGLE: each tile/position is a separate ``LifImage``.
    MOSAIC: all positions are stored within a single ``LifImage``.
    """

    SINGLE = "single"
    MOSAIC = "mosaic"

    @classmethod
    def from_metadata(cls, metadata: dict) -> "ImageType":
        """Get image type from a LIF metadata dict."""
        if "mosaic_position" in metadata and len(metadata["mosaic_position"]) > 0:
            return cls.MOSAIC
        return cls.SINGLE


class _ImageInPlateInfo(BaseModel):
    """Image record for plate-mode acquisitions (private to lif/)."""

    image_id: int
    image_type: ImageType
    scan_name: str
    row: str
    column: str
    acquisition_id: int
    position_name: str | None = None


class _ImageInfo(BaseModel):
    """Image record for single (non-plate) acquisitions (private to lif/)."""

    image_id: int
    image_type: ImageType
    scan_name: str
    position_name: str | None = None


# ---------------------------------------------------------------------------
# XML helpers — recover stage position metadata for non-mosaic LIF images.
# ---------------------------------------------------------------------------


@cache
def _get_xml(path: str):
    return get_xml(path)[0]


@cache
def _inner_find_nested_element(xml_elem, name):
    found = None
    # Iter('Element') includes the current node when it matches; skip it
    # so we only descend into children.
    for elem in xml_elem.iter("Element"):
        if elem is xml_elem:
            continue
        if elem.attrib.get("Name") == name:
            found = elem
            break
    return found


def _find_nested_element(xml_path: str, name: str):
    """Walk the LIF XML tree to find an <Element> by its hierarchical name."""
    current_node = _get_xml(xml_path)
    for part in name.split("/"):
        found = _inner_find_nested_element(current_node, part)
        if found is None:
            return None
        current_node = found
    return current_node


@cache
def _remove_nested_elements(element):
    for child in list(element):
        if child.tag == "Element":
            element.remove(child)
        else:
            _remove_nested_elements(child)
    return element


def _find_tile_infos(path: str, name: str) -> dict[str, str]:
    """Find the tile metadata for a single-position image."""
    element = _find_nested_element(path, name)
    if element is None:
        raise ValueError(f"Could not find the position metadata for {name}")
    element = _remove_nested_elements(element)
    tiles: list[dict] = []
    for child in element.iter():
        if child.tag == "Tile":
            tiles.append(dict(child.attrib))

    if len(tiles) == 0:
        raise ValueError(f"Could not find the position metadata for {name}")

    if len(tiles) > 1:
        raise ValueError(
            f"Found multiple tiles position for {name}. "
            "But the image is not a mosaic. This case is not supported."
        )
    return tiles[0]


# ---------------------------------------------------------------------------
# Tile constructors
# ---------------------------------------------------------------------------


def _resolve_scale_m(lif_image: Any, scale_m: float | None) -> float:
    if scale_m is not None:
        return scale_m
    return lif_image.scale_n.get(10, 1e-6)


def _shape_5d(lif_image: Any) -> tuple[int, int, int, int, int]:
    shape_x = lif_image.dims_n.get(1, 1)
    shape_y = lif_image.dims_n.get(2, 1)
    shape_z = lif_image.dims_n.get(3, 1)
    shape_t = lif_image.dims_n.get(4, 1)
    shape_c = lif_image.channels
    return shape_t, shape_c, shape_z, shape_y, shape_x


def _build_mosaic_tiles(
    *,
    lif_image: Any,
    image_id: int,
    collection: ImageInPlate | SingleImage,
    acquisition_details: AcquisitionDetails,
    scale_m: float | None,
) -> list[Tile]:
    shape_t, shape_c, shape_z, shape_y, shape_x = _shape_5d(lif_image)
    scale = _resolve_scale_m(lif_image, scale_m)

    tiles: list[Tile] = []
    for m, pos in enumerate(lif_image.mosaic_position):
        x_um = pos[2] / scale
        y_um = pos[3] / scale
        loader = LifMosaicLoader(
            file_path=lif_image.filename,
            image_id=image_id,
            m=m,
        )
        tiles.append(
            Tile(
                fov_name=f"FOV_{m}",
                start_x=x_um,
                start_y=y_um,
                start_z=0,
                start_c=0,
                start_t=0,
                length_x=shape_x,
                length_y=shape_y,
                length_z=shape_z,
                length_c=shape_c,
                length_t=shape_t,
                collection=collection,
                image_loader=loader,
                acquisition_details=acquisition_details,
                attributes={},
            )
        )
    return tiles


def _build_single_tile(
    *,
    lif_image: Any,
    image_id: int,
    fov_name: str,
    collection: ImageInPlate | SingleImage,
    acquisition_details: AcquisitionDetails,
    scale_m: float | None,
) -> Tile:
    shape_t, shape_c, shape_z, shape_y, shape_x = _shape_5d(lif_image)
    scale = _resolve_scale_m(lif_image, scale_m)

    tile_info = _find_tile_infos(lif_image.filename, lif_image.name)
    x_um = float(tile_info.get("PosX", 0)) / scale
    y_um = float(tile_info.get("PosY", 0)) / scale

    loader = LifSingleLoader(
        file_path=lif_image.filename,
        image_id=image_id,
    )
    return Tile(
        fov_name=fov_name,
        start_x=x_um,
        start_y=y_um,
        start_z=0,
        start_c=0,
        start_t=0,
        length_x=shape_x,
        length_y=shape_y,
        length_z=shape_z,
        length_c=shape_c,
        length_t=shape_t,
        collection=collection,
        image_loader=loader,
        acquisition_details=acquisition_details,
        attributes={},
    )


def _single_fov_name(
    info: _ImageInPlateInfo | _ImageInfo, idx: int, *, multi: bool
) -> str:
    if not multi:
        return "FOV_0"
    if info.position_name:
        return f"FOV_{info.position_name}"
    return f"FOV_{idx}"


def build_plate_acq_tiles(
    *,
    lif_file: LifFile,
    image_infos: list[_ImageInPlateInfo],
    plate_name: str,
    acquisition_id: int,
    acquisition_details_factory: Callable[[Any], AcquisitionDetails],
    scale_m: float | None,
) -> list[Tile]:
    """Build ``Tile`` objects for one plate-mode well/position group.

    Args:
        lif_file: Open LIF file handle.
        image_infos: Image records belonging to a single
            ``(scan_name, row, column, acquisition_id)`` group. Mosaic groups
            must contain exactly one record; single groups may contain many.
        plate_name: Plate name for the ``ImageInPlate`` collection.
        acquisition_id: Acquisition identifier within the plate.
        acquisition_details_factory: Callable producing ``AcquisitionDetails``
            for a given ``LifImage``. The factory is responsible for
            channel/pixelsize/data-type metadata.
        scale_m: Override for the LIF metres-per-micrometre scale; falls back
            to ``lif_image.scale_n.get(10, 1e-6)`` per image when ``None``.

    Returns:
        Flat list of tiles for this group.
    """
    if not image_infos:
        return []

    image_type = image_infos[0].image_type
    if image_type is ImageType.MOSAIC:
        if len(image_infos) != 1:
            raise ValueError(
                "Only one mosaic image is expected per plate position. "
                "Multi-mosaic is not supported."
            )
        info = image_infos[0]
        lif_image = lif_file.get_image(info.image_id)
        collection = ImageInPlate(
            plate_name=plate_name,
            row=info.row,
            column=int(info.column),
            acquisition=acquisition_id,
        )
        return _build_mosaic_tiles(
            lif_image=lif_image,
            image_id=info.image_id,
            collection=collection,
            acquisition_details=acquisition_details_factory(lif_image),
            scale_m=scale_m,
        )

    multi = len(image_infos) > 1
    tiles: list[Tile] = []
    for idx, info in enumerate(image_infos):
        lif_image = lif_file.get_image(info.image_id)
        collection = ImageInPlate(
            plate_name=plate_name,
            row=info.row,
            column=int(info.column),
            acquisition=acquisition_id,
        )
        tiles.append(
            _build_single_tile(
                lif_image=lif_image,
                image_id=info.image_id,
                fov_name=_single_fov_name(info, idx, multi=multi),
                collection=collection,
                acquisition_details=acquisition_details_factory(lif_image),
                scale_m=scale_m,
            )
        )
    return tiles


def build_single_acq_tiles(
    *,
    lif_file: LifFile,
    image_infos: list[_ImageInfo],
    image_path: str,
    acquisition_details_factory: Callable[[Any], AcquisitionDetails],
    scale_m: float | None,
) -> list[Tile]:
    """Build ``Tile`` objects for a single (non-plate) acquisition group.

    Args:
        lif_file: Open LIF file handle.
        image_infos: Image records belonging to one acquisition group.
            Mosaic groups must contain exactly one record; single groups may
            contain one (single FOV) or many (multi-position).
        image_path: Value used for ``SingleImage.image_path``.
        acquisition_details_factory: Callable producing ``AcquisitionDetails``
            for a given ``LifImage``.
        scale_m: Override for the LIF metres-per-micrometre scale; falls back
            to ``lif_image.scale_n.get(10, 1e-6)`` per image when ``None``.

    Returns:
        Flat list of tiles for this group.
    """
    if not image_infos:
        return []

    image_type = image_infos[0].image_type
    collection = SingleImage(image_path=image_path)
    if image_type is ImageType.MOSAIC:
        if len(image_infos) != 1:
            raise ValueError(
                "Only one mosaic image is expected per acquisition. "
                "Multi-mosaic is not supported."
            )
        info = image_infos[0]
        lif_image = lif_file.get_image(info.image_id)
        return _build_mosaic_tiles(
            lif_image=lif_image,
            image_id=info.image_id,
            collection=collection,
            acquisition_details=acquisition_details_factory(lif_image),
            scale_m=scale_m,
        )

    multi = len(image_infos) > 1
    tiles: list[Tile] = []
    for idx, info in enumerate(image_infos):
        lif_image = lif_file.get_image(info.image_id)
        tiles.append(
            _build_single_tile(
                lif_image=lif_image,
                image_id=info.image_id,
                fov_name=_single_fov_name(info, idx, multi=multi),
                collection=collection,
                acquisition_details=acquisition_details_factory(lif_image),
                scale_m=scale_m,
            )
        )
    return tiles
