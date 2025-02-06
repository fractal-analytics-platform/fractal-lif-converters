"""Module for parsing LIF files with plate scans."""

from pathlib import Path

from fractal_converters_tools.tiled_image import (
    TiledImage,
)
from readlif.reader import LifFile

from fractal_lif_converters.string_validation import (
    validate_position_name_type1,
    validate_well_name_type1,
    validate_well_name_type2,
)
from fractal_lif_converters.tile_builders import (
    ImageInPlateInfo,
    ImageType,
    collect_plate_acq_mosaic,
    collect_plate_acq_single,
)


def _parse_lif_plate_infos(
    lif_file: LifFile, scan_name: str | None = None, acquisition_id: int = 0
):
    """Parse Lif file and return image information."""
    if scan_name is None and acquisition_id != 0:
        raise ValueError("acquisition_id should be 0 if no scan_name is not provided.")

    plates, discarded_images = {}, []
    for image_id, meta in enumerate(lif_file.image_list):
        name = meta["name"]
        _scan_name, *other = name.split("/")
        if scan_name is not None and scan_name != _scan_name:
            # Unless we are in wildcard mode
            # skip images that do not match the scan name in the query
            continue

        if _scan_name not in plates:
            plates[_scan_name] = []

        image_in_plate_info = None
        if len(other) == 1:
            # Cases to cover here:
            # - "A1"
            test_well_name, row, col = validate_well_name_type1(other[0])
            if test_well_name:
                image_in_plate_info = ImageInPlateInfo(
                    image_id=image_id,
                    image_type=ImageType.from_metadata(meta),
                    scan_name=_scan_name,
                    row=row,
                    column=col,
                    acquisition_id=acquisition_id,
                )
        elif len(other) == 2:
            # Cases to cover here:
            # - "A/1"
            row, col = other
            test_well_name, row, col = validate_well_name_type2(
                row_name=row, column_name=col
            )
            if test_well_name:
                image_in_plate_info = ImageInPlateInfo(
                    image_id=image_id,
                    image_type=ImageType.from_metadata(meta),
                    scan_name=_scan_name,
                    row=row,
                    column=col,
                    acquisition_id=acquisition_id,
                )

        elif len(other) == 2:
            # - "A1/R1"
            well_name, position_name = other
            test_well_name, row, col = validate_well_name_type2(well_name)
            test_pos_name, position_name = validate_position_name_type1(position_name)
            if test_well_name and test_pos_name:
                image_in_plate_info = ImageInPlateInfo(
                    image_id=image_id,
                    image_type=ImageType.from_metadata(meta),
                    scan_name=_scan_name,
                    row=row,
                    column=col,
                    acquisition_id=acquisition_id,
                )

        elif len(other) == 3:
            # Cases to cover here:
            # - "A/1/R1"
            row, col, position_name = other
            test_well_name, row, col = validate_well_name_type2(
                row_name=row, column_name=col
            )
            test_pos_name, position_name = validate_position_name_type1(position_name)
            if test_well_name and test_pos_name:
                image_in_plate_info = ImageInPlateInfo(
                    image_id=image_id,
                    image_type=ImageType.from_metadata(meta),
                    scan_name=_scan_name,
                    row=row,
                    column=col,
                    acquisition_id=acquisition_id,
                )

        if image_in_plate_info:
            plates[_scan_name].append(image_in_plate_info)
        else:
            discarded_images.append(name)

    if len(discarded_images) == len(lif_file.image_list):
        msg = (
            f"No valid images found in the Lif file at path: {lif_file.filename}. "
            f"Please check if the lif layout is supported by this converter."
        )
        raise ValueError(msg)

    # Remove empty scans from the plates
    # This can happen in case of wildcard mode where not
    # all scans are plates
    _scan_to_delete = []
    for scan_name, images in plates.items():
        if len(images) == 0:
            _scan_to_delete.append(scan_name)

    for scan_name in _scan_to_delete:
        del plates[scan_name]

    # If no plates are found, raise an error
    if len(plates) == 0:
        msg = (
            f"No valid images found in the Lif file at path: {lif_file.filename}. \n"
            f"Please check if the lif layout is supported by this converter."
        )
        raise ValueError(msg)

    if len(discarded_images) > 0:
        print(f"Discarded images: {discarded_images}")

    return plates


def group_by_tile_id(
    image_infos: list[ImageInPlateInfo],
) -> list[list[ImageInPlateInfo]]:
    """Group image infos by tile id."""
    tile_id_to_images = {}
    for image_info in image_infos:
        if image_info.tile_id not in tile_id_to_images:
            tile_id_to_images[image_info.tile_id] = []
        tile_id_to_images[image_info.tile_id].append(image_info)
    return list(tile_id_to_images.values())


def parse_lif_plate_metadata(
    lif_path: str | Path,
    scan_name: str | None = None,
    plate_name: str | None = None,
    acquisition_id: int = 0,
    channel_names: list[str] | None = None,
    channel_wavelengths: list[str] | None = None,
    scale_m: float | None = None,
) -> dict[str, TiledImage]:
    """Parse lif metadata."""
    if scan_name is None and plate_name is not None:
        raise ValueError(
            "'plate_name' cannot be provided for wildcard mode. \n"
            "To set custom plate name, please provide 'scan_name' as well."
        )

    lif_file = LifFile(lif_path)
    plates = _parse_lif_plate_infos(lif_file, scan_name, acquisition_id)

    tiled_images = {}
    for scan_name, image_infos in plates.items():
        if plate_name is None:
            _plate_name = f"{Path(lif_path).stem}_{scan_name}"
            _plate_name = _plate_name.replace(" ", "_")
        else:
            _plate_name = plate_name

        for list_image_infos in group_by_tile_id(image_infos):
            if len(list_image_infos) == 0:
                raise ValueError("No images found for the given tile id.")
            image_type = list_image_infos[0].image_type
            match image_type:
                case ImageType.SINGLE:
                    _tiled_image = collect_plate_acq_single(
                        lif_file=lif_file,
                        image_infos=list_image_infos,
                        plate_name=_plate_name,
                        channel_names=channel_names,
                        channel_wavelengths=channel_wavelengths,
                        scale_m=scale_m,
                    )
                case ImageType.MOSAIC:
                    _tiled_image = collect_plate_acq_mosaic(
                        lif_file=lif_file,
                        image_infos=list_image_infos,
                        plate_name=_plate_name,
                        channel_names=channel_names,
                        channel_wavelengths=channel_wavelengths,
                        scale_m=scale_m,
                    )
            unique_id = f"{plate_name}_{list_image_infos[0].tile_id}"
            tiled_images[unique_id] = _tiled_image
    return tiled_images
