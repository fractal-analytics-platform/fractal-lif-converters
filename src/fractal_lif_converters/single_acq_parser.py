"""Module for parsing LIF files with plate scans."""

from pathlib import Path  # noqa: I001

from fractal_converters_tools.tiled_image import (
    TiledImage,
)
from readlif.reader import LifFile

from fractal_lif_converters.string_validation import (
    validate_position_name_type2,
    validate_position_name_type1,
)
from fractal_lif_converters.tile_builders import (
    ImageInfo,
    ImageType,
    collect_single_acq_mosaic,
    collect_single_acq_single,
)
import logging

logger = logging.getLogger(__name__)


def _simple_parse_lif_infos(
    lif_file: LifFile, scan_name: str
) -> tuple[dict[str, list[ImageInfo]], set[str]]:
    images = []

    discarder_images = []
    _sanitized_scan_name = scan_name.replace(" ", "_")
    _sanitized_scan_name = _sanitized_scan_name.replace("/", "_")

    for image_id, meta in enumerate(lif_file.image_list):
        name = meta["name"]
        if name == scan_name:
            image_info = ImageInfo(
                image_id=image_id,
                image_type=ImageType.from_metadata(meta),
                scan_name=_sanitized_scan_name,
            )
            images.append(image_info)
            break
        elif name.startswith(scan_name):
            pos_suffix = name.removeprefix(scan_name)
            pos_suffix = pos_suffix.lstrip("/")
            test_pos1, _ = validate_position_name_type2(pos_suffix)
            test_pos2, _ = validate_position_name_type1(pos_suffix)
            test_pos_name = test_pos1 or test_pos2
            if test_pos_name:
                image_info = ImageInfo(
                    image_id=image_id,
                    image_type=ImageType.from_metadata(meta),
                    scan_name=_sanitized_scan_name,
                )
                images.append(image_info)
            else:
                discarder_images.append(name)
        else:
            pass

    if len(images) == 0:
        msg = (
            f"Tile Scan {scan_name} not found in the Lif file at path: "
            f"{lif_file.filename}. \n"
        )
        raise ValueError(msg)

    return {_sanitized_scan_name: images}, set(discarder_images)


def _wildcard_parse_lif_infos(
    lif_file: LifFile,
) -> tuple[dict[str, list[ImageInfo]], set[str]]:
    """Parse Lif file and return image information."""
    base_scan_names = set()
    discarder_images = set()
    for meta in lif_file.image_list:
        name = meta["name"]
        scans = name.split("/")
        if len(scans) == 0:
            raise ValueError(f"Invalid scan name: {name}")

        elif len(scans) == 1:
            base_scan_names.add(scans[0])

        elif len(scans) >= 2:
            base, *_, pos_suffix = scans
            test_pos1, _ = validate_position_name_type2(pos_suffix)
            test_pos2, _ = validate_position_name_type1(pos_suffix)
            test_pos_name = test_pos1 or test_pos2
            if test_pos_name:
                base = "/".join(scans[:-1])
                base_scan_names.add(base)
            elif ImageType.from_metadata(meta) == ImageType.MOSAIC:
                base_scan_names.add(name)
            else:
                discarder_images.add(name)
        else:
            raise ValueError(f"Invalid scan name: {name}")

    images = {}
    for base_scan_name in base_scan_names:
        _images, _discarded_images = _simple_parse_lif_infos(lif_file, base_scan_name)
        images.update(_images)
        _discarded_images = _discarded_images.union(_discarded_images)

    return images, discarder_images


def group_by_tile_id(
    image_infos: list[ImageInfo],
) -> list[list[ImageInfo]]:
    """Group image infos by tile id."""
    tile_id_to_images = {}
    for image_info in image_infos:
        if image_info.tile_id not in tile_id_to_images:
            tile_id_to_images[image_info.tile_id] = []
        tile_id_to_images[image_info.tile_id].append(image_info)
    return list(tile_id_to_images.values())


def parse_lif_metadata(
    lif_path: str | Path,
    scan_name: str | None = None,
    zarr_name: str | None = None,
    channel_names: list[str] | None = None,
    channel_wavelengths: list[str] | None = None,
    scale_m: float | None = None,
) -> list[TiledImage]:
    """Parse lif metadata."""
    if scan_name is None and zarr_name is not None:
        raise ValueError(
            "'zarr_name' cannot be provided for wildcard mode. \n"
            "To set custom zarr name, please provide 'scan_name' as well."
        )

    lif_file = LifFile(lif_path)

    if scan_name is not None:
        images, dis_images = _simple_parse_lif_infos(lif_file, scan_name)
    else:
        images, dis_images = _wildcard_parse_lif_infos(lif_file)

    if len(dis_images) > 0:
        logger.warning(f"Discarded images: {dis_images}")

    tiled_images = []
    for name, image_infos in images.items():
        if zarr_name is None:
            _zarr_name = f"{Path(lif_path).stem}_{name}"
            _zarr_name = _zarr_name.replace(" ", "_")
        else:
            _zarr_name = zarr_name

        _image_type = image_infos[0].image_type
        match _image_type:
            case ImageType.SINGLE:
                _tiled_image = collect_single_acq_single(
                    lif_file=lif_file,
                    image_infos=image_infos,
                    zarr_name=_zarr_name,
                    channel_names=channel_names,
                    channel_wavelengths=channel_wavelengths,
                    scale_m=scale_m,
                )
            case ImageType.MOSAIC:
                _tiled_image = collect_single_acq_mosaic(
                    lif_file=lif_file,
                    image_infos=image_infos,
                    zarr_name=_zarr_name,
                    channel_names=channel_names,
                    channel_wavelengths=channel_wavelengths,
                    scale_m=scale_m,
                )
            case _:
                raise ValueError(f"Image type {_image_type} not supported.")
        tiled_images.append(_tiled_image)
    return tiled_images
