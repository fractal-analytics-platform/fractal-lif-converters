"""Utility functions for the lif file format."""

import numpy as np
from readlif.reader import LifFile, LifImage


def find_shape_um(image: LifImage) -> tuple[float, float, float]:
    """Find the shape of the each tile in the scene in um."""
    shapes = []
    for i in [1, 2, 3]:
        if i in image.dims_n.keys():
            shapes.append(image.dims_n[i] / image.scale_n[i])
        else:
            shapes.append(0)
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
    for roi_0, roi_1 in zip(rois[:-1], rois[1:]):
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
        raise ValueError(
            "Overlapping ratio is not the same for all tiles, " "this is not supported."
        )
    return list_overlap[0]


def build_grid_mapping(image_file: LifFile) -> dict:
    """Find the appropriate grid mapping for the scene."""
    grid_mapping = {}
    for image in image_file.get_iter_image():
        tile_name = image.name
        rois = mosaic_to_overlapping_rois(image)
        overlap = compute_overalap_ratio(rois)
        new_grid = []
        for roi in rois:
            size, *_ = find_shape_um(image)
            x, y, *_ = roi["bbox_um"]
            new_g_x = int(np.round((x / size) * overlap))
            new_g_y = int(np.round((y / size) * overlap))
            new_grid.append((new_g_x, new_g_y))

        grid_mapping[tile_name] = new_grid
    return grid_mapping
