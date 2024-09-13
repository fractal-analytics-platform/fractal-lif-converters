"""High Leve utility functions for the lif converters."""

from itertools import product
from pathlib import Path

import anndata as ad
import bioio_lif
import numpy as np
import readlif
import zarr
from bioio import BioImage
from fractal_tasks_core.pyramids import build_pyramid
from fractal_tasks_core.tables import write_table
from pandas import DataFrame

from lif_converters.lif_utils import build_grid_mapping
from lif_converters.ngff_image_meta_utils import generate_ngff_metadata
from lif_converters.ngff_plate_meta_utils import (
    PlateScene,
    build_acquisition_path,
    build_well_path,
    generate_plate_metadata,
    generate_wells_metadata,
    scene_plate_iterate,
)


def setup_plate_ome_zarr(
    zarr_path: str | Path,
    img_bio: BioImage,
    num_levels: int = 5,
    coarsening_xy: float = 2.0,
    overwrite=True,
):
    """Setup the zarr structure for the plate, wells and acquisitions metadata.

    Args:
        zarr_path (str, Path): The path to the zarr store.
        img_bio (BioImage): The BioImage object.
        num_levels (int): The number of resolution levels. Defaults to 5.
        coarsening_xy (float): The scaling factor for the xy axes. Defaults to 2.0.
        overwrite (bool): If True, the zarr store will be overwritten.
            Defaults to True.
    """
    plate_metadata = generate_plate_metadata(img_bio)
    plate_group = zarr.group(store=zarr_path, overwrite=overwrite)
    plate_group.attrs.update(plate_metadata.model_dump(exclude_none=True))

    wells_meta = generate_wells_metadata(img_bio)
    for path, well in wells_meta.items():
        well_group = plate_group.create_group(path)
        well_group.attrs.update(well.model_dump(exclude_none=True))

    for scene in scene_plate_iterate(img_bio):
        img_bio.set_scene(scene.scene)
        img_bio.reader._read_immediate()
        ngff_meta = generate_ngff_metadata(
            img_bio=img_bio, num_levels=num_levels, coarsening_xy=coarsening_xy
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
    coarsening_xy: int | float = 2,
) -> tuple[str, dict, dict]:
    """This function creates the high resolution data and the pyramid for the image.

    Note that the image is assumed to be a part of a plate.

    Args:
        zarr_path (Path): The path to the zarr store (plate root).
        lif_path (Path): The path to the lif file.
        tile_name (str): The name of the scene (as stored in the lif file).
        num_levels (int): The number of resolution levels. Defaults to 5.
        coarsening_xy (int | float): The coarsening factor for the xy axes. Defaults

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
    names_order = [meta["name"] for meta in img.image_list]
    idx = names_order.index(scene.scene)
    image = img.get_image(idx)

    # Create the zarr store for the high resolution data
    acquisition_path = build_acquisition_path(
        row=scene.row, column=scene.column, acquisition=scene.acquisition_id
    )

    full_acquisition_path = f"{zarr_path}/{acquisition_path}"
    full_high_res_path = f"{full_acquisition_path}/0"

    grid, fov_rois, well_roi = build_grid_mapping(img, scene.scene)
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

    # The (i, j) needs to be reversed
    # (image internal representation is xy anz zarr is yx)
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
    coarsening_xy = int(coarsening_xy)
    acquisition_image_path = f"{zarr_path}/{acquisition_path}"
    build_pyramid(
        zarrurl=acquisition_image_path,
        num_levels=num_levels,
        coarsening_xy=coarsening_xy,
    )

    image_zarr_group = zarr.open_group(acquisition_image_path)

    # Create FOV rois Table
    foi_df = DataFrame.from_records(fov_rois)
    foi_df = foi_df.set_index("FieldIndex")
    # transform the FieldIndex to the index of the table

    foi_df.index = foi_df.index.astype(str)
    foi_df = foi_df.astype(np.float32)
    foi_ad = ad.AnnData(foi_df)

    write_table(
        image_group=image_zarr_group,
        table=foi_ad,
        table_name="FOV_ROI_table",
        table_type="roi_table",
    )

    # Create Well ROI Table
    well_df = DataFrame.from_records([well_roi])
    well_df = well_df.set_index("FieldIndex")

    well_df.index = well_df.index.astype(str)
    well_df = well_df.astype(np.float32)
    well_ad = ad.AnnData(well_df)

    write_table(
        image_group=image_zarr_group,
        table=well_ad,
        table_name="well_ROI_table",
        table_type="roi_table",
    )

    if dim.z > 1:
        is_3D = True
    else:
        is_3D = False

    types = {
        "is_3D": True if dim.z > 1 else False,
    }

    attributes = {
        "plate": "TODO",
        "well": build_well_path(scene.row, scene.column),
    }

    return str(acquisition_image_path), types, attributes
