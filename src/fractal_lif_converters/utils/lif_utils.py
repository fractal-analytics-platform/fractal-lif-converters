"""Utility functions for the lif file format."""

from itertools import pairwise

import numpy as np
from readlif.reader import LifFile, LifImage

from fractal_lif_converters.utils import LifFormatNotSupported


def find_shape_um(image: LifImage) -> tuple[float, float, float]:
    """Find the shape of the each tile in the scene in um."""
    shapes = []
    for i in [1, 2, 3]:
        if i in image.dims_n.keys():
            shapes.append(image.dims_n[i] / image.scale_n[i])
        else:
            shapes.append(1)
    return shapes


def _pos_to_um(pos, image: LifImage) -> tuple[float, float]:
    pos_x, pos_y = pos[2], pos[3]
    # Transform to um
    pos_x = pos_x / image.scale_n[10]
    pos_y = pos_y / image.scale_n[10]
    return pos_x, pos_y


def find_offsets_um(image: LifImage) -> tuple[float, float]:
    """Find the global offset of the scene in um."""
    min_x, min_y = np.inf, np.inf
    for pos in image.mosaic_position:
        pos_x, pos_y = _pos_to_um(pos, image)
        min_x = min(min_x, pos_x)
        min_y = min(min_y, pos_y)
    return min_x, min_y


def mosaic_to_overlapping_rois(image: LifImage) -> list[dict]:
    """Convert the mosaic positions in the raw metadata to overlapping rois in um."""
    shape_x, shape_y, shape_z = find_shape_um(image)
    offset_x, offset_y = find_offsets_um(image)

    rois = []
    for pos in image.mosaic_position:
        pos_x, pos_y = _pos_to_um(pos, image)
        bbox_um = (pos_x - offset_x, pos_y - offset_y, 0, shape_x, shape_y, shape_z)
        coo = (pos[0], pos[1])

        rois.append({"bbox_um": bbox_um, "coo": coo})
    return rois


def compute_overalap_ratio(rois: list[dict]) -> float:
    """Returns the overlap ratio between the tiles in the scene."""
    size_x, size_y = rois[0]["bbox_um"][3], rois[0]["bbox_um"][4]

    list_overlap = []
    for roi_0, roi_1 in pairwise(rois):
        roi_bbox_0, roi_bbox_1 = roi_0["bbox_um"], roi_1["bbox_um"]
        diff_x, diff_y = roi_bbox_1[0] - roi_bbox_0[0], roi_bbox_1[1] - roi_bbox_0[1]
        # Only one of the offsets should be non-zero
        # and the diff should be less than the size of the tile
        if diff_x > 0.0 and diff_y < 0.1 and diff_x < size_x:
            overlap = 2 - diff_x / size_x
            list_overlap.append(overlap)
        if diff_y > 0.0 and diff_x < 0.1 and diff_y < size_y:
            overlap = 2 - diff_y / size_y
            list_overlap.append(overlap)

    # check if all offsets are the same more or less
    if not np.allclose(list_overlap, list_overlap[0], atol=0.1):
        raise LifFormatNotSupported(
            "Overlapping ratio is not the same for all tiles, this is not supported."
        )
    return list_overlap[0]


def find_well_roi(fov_rois: list[dict]) -> dict:
    """Create a bounding box for the well from the fov rois."""
    min_x, min_y, min_z = np.inf, np.inf, np.inf
    max_x, max_y, max_z = -np.inf, -np.inf, -np.inf
    for roi in fov_rois:
        x, y, z = roi["x_micrometer"], roi["y_micrometer"], roi["z_micrometer"]
        len_x, len_y, len_z = (
            roi["len_x_micrometer"],
            roi["len_y_micrometer"],
            roi["len_z_micrometer"],
        )
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        min_z = min(min_z, z)

        max_x = max(max_x, x + len_x)
        max_y = max(max_y, y + len_y)
        max_z = max(max_z, z + len_z)

    well_roi = {
        "FieldIndex": "Well_1",
        "x_micrometer": min_x,
        "y_micrometer": min_y,
        "z_micrometer": min_z,
        "len_x_micrometer": max_x - min_x,
        "len_y_micrometer": max_y - min_y,
        "len_z_micrometer": max_z - min_z,
    }
    return well_roi


def build_grid_mapping_no_mosaic(
    lif_image: LifImage,
) -> tuple[list, list[dict] | None, dict]:
    """Build the grid mapping for a scene without mosaic."""
    size_x, size_y, size_z = find_shape_um(lif_image)
    well_roi = {
        "FieldIndex": "Well_1",
        "x_micrometer": 0.0,
        "y_micrometer": 0.0,
        "z_micrometer": 0.0,
        "len_x_micrometer": size_x,
        "len_y_micrometer": size_y,
        "len_z_micrometer": size_z,
    }
    return [(0, 0)], None, well_roi


def build_grid_mapping(
    image_file: LifFile, tile_name: str
) -> tuple[list, list[dict] | None, dict]:
    """Find the appropriate grid mapping for the scene."""
    list_tiles_names = [meta["name"] for meta in image_file.image_list]

    if tile_name not in list_tiles_names:
        raise ValueError(f"Tile {tile_name} not found in the image file.")

    index_tile = list_tiles_names.index(tile_name)
    image = image_file.get_image(index_tile)

    if len(image.mosaic_position) == 0:
        return build_grid_mapping_no_mosaic(image)

    rois = mosaic_to_overlapping_rois(image)
    overlap = compute_overalap_ratio(rois)
    new_grid, fov_rois = [], []
    for i, roi in enumerate(rois):
        size, size_y, size_z = find_shape_um(image)
        if not np.allclose(size, size_y):
            raise LifFormatNotSupported(
                "Tile of different size in x and y are not supported."
            )

        x, y, *_ = roi["bbox_um"]
        new_g_x = int(np.round((x / size) * overlap))
        new_g_y = int(np.round((y / size) * overlap))
        new_grid.append((new_g_x, new_g_y))

        new_x, new_y, new_z = new_g_x * size, new_g_y * size, 0

        fov_roi = {
            "FieldIndex": f"FOV_{i}",
            "x_micrometer": new_y,
            "y_micrometer": new_x,
            "z_micrometer": new_z,
            "len_x_micrometer": size,
            "len_y_micrometer": size,
            "len_z_micrometer": size_z,
            "x_micrometer_original": y,
            "y_micrometer_original": x,
        }
        fov_rois.append(fov_roi)

    well_roi = find_well_roi(fov_rois)
    return new_grid, fov_rois, well_roi
