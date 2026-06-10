"""Parse LIF image metadata into ``TiledImage`` objects."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import liffile
from ome_zarr_converters_tools import (
    AcquisitionDetails,
    ConverterOptions,
    Tile,
    TiledImage,
    default_axes_builder,
    tiles_aggregation_pipeline,
)

from fractal_lif_converters.common._string_validation import (
    validate_position_name_type1,
    validate_position_name_type2,
)
from fractal_lif_converters.common._tile_builders import (
    ImageType,
    _ImageInfo,
    build_image_tiles,
)

if TYPE_CHECKING:
    from fractal_lif_converters.lif_image.convert_lif_image_init_task import (
        LifImageAcquisitionModel,
    )

logger = logging.getLogger(__name__)


def _sanitize_scan_name(name: str) -> str:
    return name.replace(" ", "_").replace("/", "_")


def _simple_parse_lif_infos(
    lif_file: liffile.LifFile, scan_name: str
) -> tuple[dict[str, list[_ImageInfo]], set[str]]:
    """Discover scans matching ``scan_name`` (named mode).

    Accepts either an exact match or entries of the form ``{scan_name}/{pos}``
    where ``pos`` is a recognized position-name suffix.
    """
    sanitized = _sanitize_scan_name(scan_name)
    images: list[_ImageInfo] = []
    discarded: set[str] = set()

    for image_id, lif_image in enumerate(lif_file.images):
        name = lif_image.path
        if name == scan_name:
            images.append(
                _ImageInfo(
                    image_id=image_id,
                    image_type=ImageType.from_lif_image(lif_image),
                    scan_name=sanitized,
                )
            )
            break
        if name.startswith(scan_name):
            pos_suffix = name.removeprefix(scan_name).lstrip("/")
            ok1, _ = validate_position_name_type1(pos_suffix)
            ok2, _ = validate_position_name_type2(pos_suffix)
            if ok1 or ok2:
                images.append(
                    _ImageInfo(
                        image_id=image_id,
                        image_type=ImageType.from_lif_image(lif_image),
                        scan_name=sanitized,
                        position_name=pos_suffix,
                    )
                )
            else:
                discarded.add(name)

    if not images:
        raise ValueError(
            f"Tile Scan {scan_name} not found in the Lif file at path: "
            f"{lif_file.filepath}."
        )

    return {sanitized: images}, discarded


def _wildcard_parse_lif_infos(
    lif_file: liffile.LifFile,
) -> tuple[dict[str, list[_ImageInfo]], set[str]]:
    """Discover all scans (wildcard mode).

    Collects base scan names by stripping recognized position suffixes; mosaic
    images keep their full hierarchical name as the scan name.
    """
    base_scan_names: set[str] = set()
    discarded: set[str] = set()
    for lif_image in lif_file.images:
        name = lif_image.path
        scans = name.split("/")
        if not scans:
            raise ValueError(f"Invalid scan name: {name}")

        if len(scans) == 1:
            base_scan_names.add(scans[0])
            continue

        pos_suffix = scans[-1]
        ok1, _ = validate_position_name_type1(pos_suffix)
        ok2, _ = validate_position_name_type2(pos_suffix)
        if ok1 or ok2:
            base_scan_names.add("/".join(scans[:-1]))
        elif ImageType.from_lif_image(lif_image) is ImageType.MOSAIC:
            base_scan_names.add(name)
        else:
            discarded.add(name)

    images: dict[str, list[_ImageInfo]] = {}
    for base in base_scan_names:
        _images, _disc = _simple_parse_lif_infos(lif_file, base)
        images.update(_images)
        discarded |= _disc

    return images, discarded


def _pixel_size_um(lif_image: Any, dim: str) -> float:
    coords = lif_image.coords.get(dim)
    if coords is not None and len(coords) > 1:
        return abs((coords[-1] - coords[0]) / (len(coords) - 1)) * 1e6
    return 1.0


def _make_acquisition_details_factory(
    acquisition_model: LifImageAcquisitionModel,
):
    def _factory(lif_image: Any) -> AcquisitionDetails:
        scale_x = _pixel_size_um(lif_image, "X")
        scale_y = _pixel_size_um(lif_image, "Y")
        scale_z = _pixel_size_um(lif_image, "Z")
        if abs(scale_x - scale_y) > 1e-9:
            logger.warning(
                f"Pixel size x ({scale_x}) and y ({scale_y}) are not equal. "
                "Using x size for pixelsize."
            )
        shape_t = lif_image.sizes.get("T", 1)
        details = AcquisitionDetails(
            pixelsize=scale_x,
            z_spacing=scale_z,
            t_spacing=1.0,
            channels=None,
            axes=default_axes_builder(is_time_series=shape_t > 1),
            start_x_coo="world",
            length_x_coo="pixel",
            start_y_coo="world",
            length_y_coo="pixel",
            start_z_coo="pixel",
            length_z_coo="pixel",
            start_t_coo="pixel",
            length_t_coo="pixel",
        )
        return acquisition_model.advanced.update_acquisition_details(
            acquisition_details=details
        )

    return _factory


def parse_lif_image_metadata(
    *,
    acquisition_model: LifImageAcquisitionModel,
    converter_options: ConverterOptions,
) -> list[TiledImage]:
    """Parse LIF image metadata and return ``TiledImage`` objects."""
    lif_path = acquisition_model.path
    lif_file = liffile.LifFile(lif_path, squeeze=False)

    if acquisition_model.tile_scan_name is not None:
        images, discarded = _simple_parse_lif_infos(
            lif_file, acquisition_model.tile_scan_name
        )
    else:
        images, discarded = _wildcard_parse_lif_infos(lif_file)

    if discarded:
        logger.info(
            f"Discarded images: {discarded} from the Lif file at path: "
            f"{lif_file.filepath}"
        )

    lif_stem = Path(lif_path).stem
    factory = _make_acquisition_details_factory(acquisition_model)

    all_tiles: list[Tile] = []
    for scan_name, image_infos in images.items():
        if acquisition_model.zarr_name is not None:
            image_path = acquisition_model.zarr_name
        else:
            image_path = f"{lif_stem}_{scan_name}".replace(" ", "_")

        tiles = build_image_tiles(
            lif_file=lif_file,
            image_infos=image_infos,
            image_path=image_path,
            acquisition_details_factory=factory,
            scale_m=acquisition_model.advanced.position_scale,
        )
        all_tiles.extend(tiles)

    logger.info(f"Built {len(all_tiles)} tiles from {lif_path}")

    return tiles_aggregation_pipeline(
        tiles=all_tiles,
        converter_options=converter_options,
        filters=acquisition_model.advanced.filters,
        validators=None,
        resource=None,
    )
