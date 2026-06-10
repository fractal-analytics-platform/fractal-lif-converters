"""Build LIF tiles for the ome-zarr-converters-tools pipeline.

Produces flat ``list[Tile]`` per acquisition; downstream
``tiles_aggregation_pipeline`` is responsible for grouping into ``TiledImage``.
"""

from collections.abc import Callable
from enum import Enum
from typing import Any

import liffile
from ome_zarr_converters_tools import (
    AcquisitionDetails,
    ImageInPlate,
    SingleImage,
    Tile,
)
from pydantic import BaseModel

from fractal_lif_converters.common._loaders import LifMosaicLoader


class ImageType(Enum):
    """LIF image storage types.

    SINGLE: each tile/position is a separate ``LifImage``.
    MOSAIC: all positions are stored within a single ``LifImage``.
    """

    SINGLE = "single"
    MOSAIC = "mosaic"

    @classmethod
    def from_lif_image(cls, lif_image: Any) -> "ImageType":
        """Get image type from a liffile LifImage."""
        ts = lif_image.tilescan
        if ts is not None and len(ts.tiles) > 1:
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
# Tile constructors
# ---------------------------------------------------------------------------


def _resolve_scale_m(scale_m: float | None) -> float:
    return scale_m if scale_m is not None else 1e-6


def _shape_5d(lif_image: Any) -> tuple[int, int, int, int, int]:
    sizes = lif_image.sizes
    shape_x = sizes.get("X", 1)
    shape_y = sizes.get("Y", 1)
    shape_z = sizes.get("Z", 1)
    shape_t = sizes.get("T", 1)
    shape_c = sizes.get("C", 1)
    return shape_t, shape_c, shape_z, shape_y, shape_x


def _build_mosaic_tiles(
    *,
    lif_image: Any,
    lif_file: Any,
    image_id: int,
    collection: ImageInPlate | SingleImage,
    acquisition_details: AcquisitionDetails,
    scale_m: float | None,
) -> list[Tile]:
    shape_t, shape_c, shape_z, shape_y, shape_x = _shape_5d(lif_image)
    scale = _resolve_scale_m(scale_m)

    tiles: list[Tile] = []
    for m, tile_pos in enumerate(lif_image.tilescan.tiles):
        x_um = tile_pos["pos_x"] / scale
        y_um = tile_pos["pos_y"] / scale
        loader = LifMosaicLoader(
            file_path=str(lif_file.filepath),
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
    lif_file: Any,
    image_id: int,
    fov_name: str,
    collection: ImageInPlate | SingleImage,
    acquisition_details: AcquisitionDetails,
    scale_m: float | None,
) -> Tile:
    shape_t, shape_c, shape_z, shape_y, shape_x = _shape_5d(lif_image)
    scale = _resolve_scale_m(scale_m)

    ts = lif_image.tilescan
    if ts is not None and len(ts.tiles) > 0:
        tile_pos = ts.tiles[0]
        x_um = tile_pos["pos_x"] / scale
        y_um = tile_pos["pos_y"] / scale
    else:
        x_um, y_um = 0.0, 0.0

    loader = LifMosaicLoader(
        file_path=str(lif_file.filepath),
        image_id=image_id,
        m=0,
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
    lif_file: liffile.LifFile,
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
            to ``1e-6`` (metres per micrometre) when ``None``.

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
        lif_image = lif_file.images[info.image_id]
        collection = ImageInPlate(
            plate_name=plate_name,
            row=info.row,
            column=int(info.column),
            acquisition=acquisition_id,
        )
        return _build_mosaic_tiles(
            lif_image=lif_image,
            lif_file=lif_file,
            image_id=info.image_id,
            collection=collection,
            acquisition_details=acquisition_details_factory(lif_image),
            scale_m=scale_m,
        )

    multi = len(image_infos) > 1
    tiles: list[Tile] = []
    for idx, info in enumerate(image_infos):
        lif_image = lif_file.images[info.image_id]
        collection = ImageInPlate(
            plate_name=plate_name,
            row=info.row,
            column=int(info.column),
            acquisition=acquisition_id,
        )
        tiles.append(
            _build_single_tile(
                lif_image=lif_image,
                lif_file=lif_file,
                image_id=info.image_id,
                fov_name=_single_fov_name(info, idx, multi=multi),
                collection=collection,
                acquisition_details=acquisition_details_factory(lif_image),
                scale_m=scale_m,
            )
        )
    return tiles


def build_image_tiles(
    *,
    lif_file: liffile.LifFile,
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
            to ``1e-6`` (metres per micrometre) when ``None``.

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
        lif_image = lif_file.images[info.image_id]
        return _build_mosaic_tiles(
            lif_image=lif_image,
            lif_file=lif_file,
            image_id=info.image_id,
            collection=collection,
            acquisition_details=acquisition_details_factory(lif_image),
            scale_m=scale_m,
        )

    multi = len(image_infos) > 1
    tiles: list[Tile] = []
    for idx, info in enumerate(image_infos):
        lif_image = lif_file.images[info.image_id]
        tiles.append(
            _build_single_tile(
                lif_image=lif_image,
                lif_file=lif_file,
                image_id=info.image_id,
                fov_name=_single_fov_name(info, idx, multi=multi),
                collection=collection,
                acquisition_details=acquisition_details_factory(lif_image),
                scale_m=scale_m,
            )
        )
    return tiles
