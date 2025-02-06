"""Module for parsing LIF files with plate scans."""

from pathlib import Path

from fractal_converters_tools.tiled_image import (
    TiledImage,
)
from readlif.reader import LifFile

from fractal_lif_converters.string_validation import (
    validate_position_name_type2,
)
from fractal_lif_converters.tile_builders import (
    ImageInfo,
    ImageType,
    collect_single_acq_mosaic,
    collect_single_acq_single,
)


def _parse_lif_infos(lif_file: LifFile, scan_name: str) -> list[ImageInfo]:
    """Parse Lif file and return image information."""
    images = []
    _scan_names = []
    for image_id, meta in enumerate(lif_file.image_list):
        name = meta["name"]
        if name.startswith(scan_name):
            *_scan_name, pos = name.split("/")

            test_pos_name, position_name = validate_position_name_type2(pos)
            if test_pos_name:
                _scan_name = "/".join(_scan_name)
            else:
                _scan_name = name

            _scan_name = _scan_name.replace(" ", "_")
            _scan_name = _scan_name.replace("/", "_")
            image_info = ImageInfo(
                image_id=image_id,
                image_type=ImageType.from_metadata(meta),
                scan_name=_scan_name,
            )
            images.append(image_info)
            _scan_names.append(_scan_name)

    if len(set(_scan_names)) > 1:
        msg = (
            f"Query scan name {scan_name} is ambiguous. "
            f"Found multiple scan names: {set(_scan_names)} in the Lif file."
        )
        raise ValueError(msg)

    if len(images) == 0:
        msg = (
            f"Tile Scan {scan_name} not found in the Lif file at path: "
            f"{lif_file.filename}. \n"
        )
        raise ValueError(msg)

    return _scan_names[0], images


def _parse_lif_multi_infos(lif_file: LifFile, scan_name: str | None = None):
    """Parse Lif file and return image information."""
    images = {}

    if scan_name is not None:
        _scan_name, _images = _parse_lif_infos(lif_file, scan_name)
        images[_scan_name] = _images
    else:
        for meta in lif_file.image_list:
            name = meta["name"]
            _scan_name, _images = _parse_lif_infos(lif_file, name)
            images[_scan_name] = _images
    if len(images) == 0:
        msg = (
            f"Tile Scan {scan_name} not found in the Lif file at path: "
            f"{lif_file.filename}. \n"
        )
        raise ValueError(msg)

    return images


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
    num_levels: int = 5,
) -> dict[str, TiledImage]:
    """Parse lif metadata."""
    if scan_name is None and zarr_name is not None:
        raise ValueError(
            "'zarr_name' cannot be provided for wildcard mode. \n"
            "To set custom zarr name, please provide 'scan_name' as well."
        )

    lif_file = LifFile(lif_path)
    images = _parse_lif_multi_infos(lif_file, scan_name)

    tiled_images = {}
    for scan_name, image_infos in images.items():
        if zarr_name is None:
            _zarr_name = f"{Path(lif_path).stem}_{scan_name}"
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
                )
            case ImageType.MOSAIC:
                _tiled_image = collect_single_acq_mosaic(
                    lif_file=lif_file,
                    image_infos=image_infos,
                    zarr_name=_zarr_name,
                    channel_names=channel_names,
                    channel_wavelengths=channel_wavelengths,
                )
        unique_id = f"{zarr_name}_{image_infos[0].tile_id}"
        tiled_images[unique_id] = _tiled_image
    return tiled_images
