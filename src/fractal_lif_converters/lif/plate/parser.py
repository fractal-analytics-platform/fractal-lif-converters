"""Parse LIF plate-mode metadata into ``TiledImage`` objects."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ome_zarr_converters_tools import (
    AcquisitionDetails,
    ConverterOptions,
    Tile,
    TiledImage,
    default_axes_builder,
    tiles_aggregation_pipeline,
)
from readlif.reader import LifFile

from fractal_lif_converters.lif.string_validation import (
    validate_position_name_type1,
    validate_well_name_type1,
    validate_well_name_type2,
)
from fractal_lif_converters.lif.tile_builders import (
    ImageType,
    _ImageInPlateInfo,
    build_plate_acq_tiles,
)

if TYPE_CHECKING:
    from fractal_lif_converters.lif.plate.convert_lif_plate_init_task import (
        LifPlateAcquisitionModel,
    )

logger = logging.getLogger(__name__)


def _parse_lif_plate_infos(
    lif_file: LifFile,
    scan_name: str | None,
    acquisition_id: int,
) -> dict[str, list[_ImageInPlateInfo]]:
    """Discover plate images grouped by scan name.

    Walks ``lif_file.image_list`` and classifies each entry against the
    supported well-name layouts. Records that don't fit any layout are
    discarded (logged for visibility).
    """
    plates: dict[str, list[_ImageInPlateInfo]] = {}
    discarded_images: list[str] = []
    for image_id, meta in enumerate(lif_file.image_list):
        name = meta["name"]
        _scan_name, *other = name.split("/")
        if scan_name is not None and scan_name != _scan_name:
            continue

        plates.setdefault(_scan_name, [])

        info = None
        if len(other) == 1:
            ok, row, col = validate_well_name_type1(other[0])
            if ok:
                info = _ImageInPlateInfo(
                    image_id=image_id,
                    image_type=ImageType.from_metadata(meta),
                    scan_name=_scan_name,
                    row=row,
                    column=col,
                    acquisition_id=acquisition_id,
                )
        elif len(other) == 2:
            # "A/1"
            row, col = other
            ok, row, col = validate_well_name_type2(row_name=row, column_name=col)
            if ok:
                info = _ImageInPlateInfo(
                    image_id=image_id,
                    image_type=ImageType.from_metadata(meta),
                    scan_name=_scan_name,
                    row=row,
                    column=col,
                    acquisition_id=acquisition_id,
                )
            else:
                # "A1/R1"
                well_name, position_name = other
                ok_well, row, col = validate_well_name_type1(well_name)
                ok_pos, position_name = validate_position_name_type1(position_name)
                if ok_well and ok_pos:
                    info = _ImageInPlateInfo(
                        image_id=image_id,
                        image_type=ImageType.from_metadata(meta),
                        scan_name=_scan_name,
                        row=row,
                        column=col,
                        acquisition_id=acquisition_id,
                        position_name=position_name,
                    )
        elif len(other) == 3:
            # "A/1/R1"
            row, col, position_name = other
            ok_well, row, col = validate_well_name_type2(row_name=row, column_name=col)
            ok_pos, position_name = validate_position_name_type1(position_name)
            if ok_well and ok_pos:
                info = _ImageInPlateInfo(
                    image_id=image_id,
                    image_type=ImageType.from_metadata(meta),
                    scan_name=_scan_name,
                    row=row,
                    column=col,
                    acquisition_id=acquisition_id,
                    position_name=position_name,
                )

        if info is not None:
            plates[_scan_name].append(info)
        else:
            discarded_images.append(name)

    if len(discarded_images) == len(lif_file.image_list):
        raise ValueError(
            f"No valid images found in the Lif file at path: {lif_file.filename}. "
            "Please check if the lif layout is supported by this converter."
        )

    plates = {k: v for k, v in plates.items() if v}

    if not plates:
        raise ValueError(
            f"No valid images found in the Lif file at path: {lif_file.filename}. "
            "Please check if the lif layout is supported by this converter."
        )

    if discarded_images:
        logger.info(
            f"Discarded images: {discarded_images} from the Lif file at path: "
            f"{lif_file.filename}"
        )

    return plates


def _group_by_well(
    image_infos: list[_ImageInPlateInfo],
) -> list[list[_ImageInPlateInfo]]:
    grouped: dict[tuple[str, str, int], list[_ImageInPlateInfo]] = {}
    for info in image_infos:
        key = (info.row, info.column, info.acquisition_id)
        grouped.setdefault(key, []).append(info)
    return list(grouped.values())


def _make_acquisition_details_factory(
    acquisition_model: LifPlateAcquisitionModel,
):
    def _factory(lif_image: Any) -> AcquisitionDetails:
        scale_x = 1 / lif_image.scale_n.get(1, 1)
        scale_y = 1 / lif_image.scale_n.get(2, 1)
        scale_z = 1 / lif_image.scale_n.get(3, 1)
        if abs(scale_x - scale_y) > 1e-9:
            logger.warning(
                f"Pixel size x ({scale_x}) and y ({scale_y}) are not equal. "
                "Using x size for pixelsize."
            )
        shape_t = lif_image.dims_n.get(4, 1)
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


def parse_lif_plate_metadata(
    *,
    acquisition_model: LifPlateAcquisitionModel,
    converter_options: ConverterOptions,
) -> list[TiledImage]:
    """Parse LIF plate metadata and return a list of ``TiledImage`` objects."""
    lif_path = acquisition_model.path
    lif_file = LifFile(lif_path)
    plates = _parse_lif_plate_infos(
        lif_file,
        scan_name=acquisition_model.tile_scan_name,
        acquisition_id=acquisition_model.acquisition_id,
    )

    lif_stem = Path(lif_path).stem
    factory = _make_acquisition_details_factory(acquisition_model)

    all_tiles: list[Tile] = []
    for scan_name, image_infos in plates.items():
        if acquisition_model.plate_name is not None:
            plate_name = acquisition_model.plate_name
        else:
            plate_name = f"{lif_stem}_{scan_name}".replace(" ", "_")

        for group in _group_by_well(image_infos):
            tiles = build_plate_acq_tiles(
                lif_file=lif_file,
                image_infos=group,
                plate_name=plate_name,
                acquisition_id=acquisition_model.acquisition_id,
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
