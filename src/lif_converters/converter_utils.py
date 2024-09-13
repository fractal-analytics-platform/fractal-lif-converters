"""Utility functions for the lif converters."""

from itertools import product
from pathlib import Path

import bioio_lif
import numpy as np
import readlif
import zarr
from bioio import BioImage
from fractal_tasks_core.pyramids import build_pyramid

from lif_converters.bioio_image_utils import PlateScene, scene_plate_iterate
from lif_converters.lif_utils import build_grid_mapping
from lif_converters.ngff_image_meta_utils import generate_ngff_metadata
from lif_converters.ngff_plate_meta_utils import (
    build_acquisition_path,
    generate_plate_metadata,
    generate_wells_metadata,
)


def setup_plate_ome_zarr(
    zarr_path: str | Path,
    img_bio: BioImage,
    num_levels: int = 5,
    xy_scaling: float = 2.0,
    overwrite=True,
):
    """Setup the zarr structure for the plate, wells and acquisitions metadata.

    Args:
        zarr_path (str, Path): The path to the zarr store.
        img_bio (BioImage): The BioImage object.
        num_levels (int, optional): The number of resolution levels. Defaults to 5.
        xy_scaling (float, optional): The scaling factor for the xy axes. Defaults to 2.0.
        overwrite (bool, optional): If True, the zarr store will be overwritten.
            Defaults to True.
    """
    plate_group = zarr.group(store=zarr_path, overwrite=overwrite)
    plate_group.attrs.update(
        generate_plate_metadata(img_bio).model_dump(exclude_none=True)
    )

    print("plate_group.attrs", dict(plate_group.attrs))

    wells_meta = generate_wells_metadata(img_bio)
    for path, well in wells_meta.items():
        well_group = plate_group.create_group(path)
        well_group.attrs.update(well.model_dump(exclude_none=True))

    for scene in scene_plate_iterate(img_bio):
        img_bio.set_scene(scene.scene)
        img_bio.reader._read_immediate()
        ngff_meta = generate_ngff_metadata(
            img_bio=img_bio, n_levels=num_levels, xy_scaling=xy_scaling
        )
        acquisition_path = build_acquisition_path(
            row=scene.row, column=scene.column, acquisition=scene.acquisition_id
        )
        acquisition_group = plate_group.create_group(acquisition_path)
        acquisition_group.attrs.update(ngff_meta.model_dump(exclude_none=True))

    return plate_group


def export_plate_acquisition_to_zarr(
    zarr_path: Path,
    lif_path: Path,
    tile_name: str,
    num_levels: int = 5,
    coarsening_xy: int = 2,
):
    """This function creates the high resolution data and the pyramid for the image.

    Note that the image is assumed to be a part of a plate.

    Args:
        zarr_path (Path): The path to the zarr store (plate root).
        lif_path (Path): The path to the lif file.
        tile_name (str): The name of the scene (as stored in the lif file).
        num_levels (int, optional): The number of resolution levels. Defaults to 5.
        coarsening_xy (int, optional): The coarsening factor for the xy axes. Defaults

    """
    # Check if the zarr file exists
    if not zarr_path.exists():
        raise FileNotFoundError(f"Zarr file not found: {zarr_path}")

    if not lif_path.exists():
        raise FileNotFoundError(f"Lif file not found: {lif_path}")

    # Setup the bioio Image
    img_bio = BioImage(lif_path, reader=bioio_lif.Reader)
    scene = PlateScene(scene_name=tile_name, image=img_bio)
    img_bio.set_scene(scene.scene)
    img_bio.reader._read_immediate()

    # Find idx of the scene in the image list from the raw readlif Image
    img = readlif.reader.LifFile(lif_path)
    grid_mapping = build_grid_mapping(img)
    names_order = [meta["name"] for meta in img.image_list]
    idx = names_order.index(scene.scene)
    image = img.get_image(idx)

    # Create the zarr store for the high resolution data
    acquisition_path = build_acquisition_path(
        row=scene.row, column=scene.column, acquisition=scene.acquisition_id
    )

    full_acquisition_path = f"{zarr_path}/{acquisition_path}"
    full_high_res_path = f"{full_acquisition_path}/0"

    grid = grid_mapping[scene.scene]
    grid_size_y, grid_size_x = np.max(grid, axis=0) + 1

    dim = image.dims
    num_channels = image.channels
    size_x, size_y = dim.x, dim.y

    array_shape = [
        dim.t,
        num_channels,
        dim.z,
        grid_size_y * size_y,
        grid_size_x * size_x,
    ]
    chunk_shape = [1, 1, 1, dim.y, dim.x]

    if dim.t == 1:
        # Remove the time dimension
        array_shape = array_shape[1:]
        chunk_shape = chunk_shape[1:]

    high_res_array = zarr.empty(
        store=full_high_res_path,
        shape=array_shape,
        dtype=img_bio.dtype,
        dimension_separator="/",
        chunks=chunk_shape,
    )

    for m, (j, i) in enumerate(grid):
        for _t, _c, _z in product(range(dim.t), range(num_channels), range(dim.z)):
            frame = image.get_frame(t=_t, c=_c, z=_z, m=m)

            if dim.t == 1:
                slices = (
                    _c,
                    _z,
                    slice(i * size_y, (i + 1) * size_y),
                    slice(j * size_x, (j + 1) * size_x),
                )
            else:
                slices = (
                    _t,
                    _c,
                    _z,
                    slice(i * size_y, (i + 1) * size_y),
                    slice(j * size_x, (j + 1) * size_x),
                )

            high_res_array[slices] = frame

    # Build the pyramid for the high resolution data
    full_res_path = f"{zarr_path}/{acquisition_path}"
    build_pyramid(
        zarrurl=full_res_path, num_levels=num_levels, coarsening_xy=coarsening_xy
    )
