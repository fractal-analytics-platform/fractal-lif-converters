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
from fractal_tasks_core.utils import logger
from pandas import DataFrame

from fractal_lif_converters.utils.lif_utils import build_grid_mapping
from fractal_lif_converters.utils.ngff_image_meta_utils import generate_ngff_metadata
from fractal_lif_converters.utils.ngff_plate_meta_utils import (
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
    coarsening_xy: int | float = 2.0,
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
    coarsening_xy = float(coarsening_xy)

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
        acquisition_group.attrs.update(ngff_meta)

    logger.info(f"Created zarr store at {zarr_path}")
    return plate_group


def _write_rois_table(
    image_group: zarr.hierarchy.Group, rois: list[dict], table_name: str
):
    """Write the ROIs table to the zarr store.

    Args:
        image_group (zarr.hierarchy.Group): The zarr group.
        rois (list[dict]): The list of ROIs.
        table_name (str): The name of the table.
    """
    roi_df = DataFrame.from_records(rois)
    roi_df = roi_df.set_index("FieldIndex")
    # transform the FieldIndex to the index of the table

    roi_df.index = roi_df.index.astype(str)
    roi_df = roi_df.astype(np.float32)
    roi_ad = ad.AnnData(roi_df)

    write_table(
        image_group=image_group,
        table=roi_ad,
        table_name=table_name,
        table_type="roi_table",
    )


def _export_acquisition_to_zarr(
    zarr_url: Path,
    lif_path: Path,
    scene_name: str,
    num_levels: int = 5,
    coarsening_xy: int = 2,
    swap_xy_axes: bool = False,
    overwrite: bool = True,
) -> tuple[str, dict, dict]:
    """This function creates the high resolution data and the pyramid for the image.

    Note that the image is assumed to be a part of a plate.

    Args:
        zarr_url (Path): The path to the zarr store (ngff image).
        lif_path (Path): The path to the lif file.
        scene_name (str): The name of the scene (as stored in the lif file).
        num_levels (int): The number of resolution levels. Defaults to 5.
        coarsening_xy (int | float): The coarsening factor for the xy axes. Defaults
        swap_xy_axes (bool): If True, the xy axes will be swapped. Defaults to False.
        overwrite (bool): If True, the zarr store will be overwritten. Defaults to True.

    """
    # Check if the zarr file exists
    if not zarr_url.exists():
        raise FileNotFoundError(f"Zarr file not found: {zarr_url}")

    if not lif_path.exists():
        raise FileNotFoundError(f"Lif file not found: {lif_path}")

    logger.info(f"{zarr_url} - Converting {lif_path} scene {scene_name} start")

    # Setup the bioio Image
    img_bio = BioImage(lif_path, reader=bioio_lif.Reader)
    img_bio.set_scene(scene_name)
    img_bio.reader._read_immediate()

    # Find idx of the scene in the image list from the raw readlif Image
    img = readlif.reader.LifFile(lif_path)
    names_order = [meta["name"] for meta in img.image_list]
    idx = names_order.index(scene_name)
    image = img.get_image(idx)

    # Build the correctly shape FOV grid
    grid, fov_rois, well_roi = build_grid_mapping(img, scene_name)
    grid_size_y, grid_size_x = np.max(grid, axis=0) + 1

    if swap_xy_axes:
        # Swap the x and y axes
        # TODO this a hack to fix the grid mapping but tables rois also need to be
        # updated
        grid_size_x, grid_size_y = grid_size_y, grid_size_x

    # Initialize the high resolution data to an empty zarr store
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
    chunk_shape = [1, 1, 1, size_y, size_x]

    if dim.t == 1:
        # Remove the time dimension
        array_shape = array_shape[1:]
        chunk_shape = chunk_shape[1:]

    full_res_zarr_url = f"{zarr_url}/0"

    high_res_array = zarr.zeros(
        store=full_res_zarr_url,
        shape=array_shape,
        dtype=img_bio.dtype,
        dimension_separator="/",
        chunks=chunk_shape,
        overwrite=overwrite,
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
    # Check if coarsening_xy is an integer or a float with a decimal part of 0
    if num_levels > 1:
        build_pyramid(
            zarrurl=zarr_url,
            num_levels=num_levels,
            coarsening_xy=int(coarsening_xy),
        )
        logger.info(f"{zarr_url} - Pyramid created with {num_levels} levels")

    else:
        logger.info(f"{zarr_url} - No pyramid created")

    mode = "a" if overwrite else "r+"
    image_zarr_group = zarr.open_group(zarr_url, mode=mode)

    # Create FOV rois Table
    if fov_rois is not None:
        _write_rois_table(
            image_group=image_zarr_group,
            rois=fov_rois,
            table_name="FOV_ROI_table",
        )
        logger.info(f"{zarr_url} - Created FOV_ROI_table")

    # Create Well ROI Table
    _write_rois_table(
        image_group=image_zarr_group,
        rois=[well_roi],
        table_name="well_ROI_table",
    )
    logger.info(f"{zarr_url} - Created well_ROI_table")

    types = {
        "is_3D": True if dim.z > 1 else False,
    }
    logger.info(f"{zarr_url} - {types['is_3D']=}")

    return types


def export_ngff_plate_acquisition(
    zarr_url: Path,
    lif_path: Path,
    scene_name: str,
    num_levels: int = 5,
    coarsening_xy: int | float = 2,
    swap_xy_axes: bool = False,
    overwrite: bool = True,
) -> tuple[str, dict, dict]:
    """This function creates the high resolution data and the pyramid for the image.

    Note that the image is assumed to be a part of a plate.

    Args:
        zarr_url (Path): The path to the zarr store (Plate root).
        lif_path (Path): The path to the lif file.
        scene_name (str): The name of the scene (as stored in the lif file).
        num_levels (int): The number of resolution levels. Defaults to 5.
        coarsening_xy (int | float): The coarsening factor for the xy axes. Defaults
        swap_xy_axes (bool): If True, the xy axes will be swapped. Defaults to False.
        overwrite (bool): If True, the zarr store will be overwritten. Defaults to True.

    """
    logger.info(f"Converting {lif_path} scene {scene_name} as a plate acquisition")
    img_bio = BioImage(lif_path, reader=bioio_lif.Reader)
    scene = PlateScene(scene_name=scene_name, image=img_bio)
    image_url = build_acquisition_path(
        row=scene.row, column=scene.column, acquisition=scene.acquisition_id
    )
    zarr_url = zarr_url / image_url

    types = _export_acquisition_to_zarr(
        zarr_url=zarr_url,
        lif_path=lif_path,
        scene_name=scene_name,
        num_levels=num_levels,
        coarsening_xy=coarsening_xy,
        swap_xy_axes=swap_xy_axes,
        overwrite=overwrite,
    )

    attributes = {
        "plate": scene.tile_name,
        "well": build_well_path(scene.row, scene.column),
    }
    return zarr_url, types, attributes


def export_ngff_single_scene(
    zarr_url: Path,
    lif_path: Path,
    scene_name: str,
    num_levels: int = 5,
    coarsening_xy: int | float = 2,
    swap_xy_axes: bool = False,
    overwrite: bool = True,
) -> tuple[str, dict, dict]:
    """This function creates the high resolution data and the pyramid for the image.

    Note that the image is assumed to be a part of a plate.

    Args:
        zarr_url (Path): The path to the zarr store (Ngff Image root).
        lif_path (Path): The path to the lif file.
        scene_name (str): The name of the scene (as stored in the lif file).
        num_levels (int): The number of resolution levels. Defaults to 5.
        swap_xy_axes (bool): If True, the xy axes will be swapped. Defaults to False.
        coarsening_xy (int | float): The coarsening factor for the xy axes. Defaults
        overwrite (bool): If True, the zarr store will be overwritten. Defaults to True.

    """
    logger.info(f"Converting {lif_path} scene {scene_name} as a single scene")
    # Crea ngff metadata
    img_bio = BioImage(lif_path, reader=bioio_lif.Reader)
    img_bio.set_scene(scene_name)
    img_bio.reader._read_immediate()

    ngff_meta = generate_ngff_metadata(
        img_bio=img_bio, num_levels=num_levels, coarsening_xy=coarsening_xy
    )

    ngff_group = zarr.group(store=zarr_url, overwrite=overwrite)
    ngff_group.attrs.update(ngff_meta)

    # Create the high resolution data and the pyramid for the image
    types = _export_acquisition_to_zarr(
        zarr_url=zarr_url,
        lif_path=lif_path,
        scene_name=scene_name,
        swap_xy_axes=swap_xy_axes,
        num_levels=num_levels,
        coarsening_xy=coarsening_xy,
        overwrite=overwrite,
    )

    return zarr_url, types, {}
