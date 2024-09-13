"""Utilities to generate OME-NGFF plate metadata from bioio.BioImage."""

from bioio import BioImage
from fractal_tasks_core import __OME_NGFF_VERSION__
from fractal_tasks_core.ngff.specs import (
    AcquisitionInPlate,
    ColumnInPlate,
    ImageInWell,
    NgffPlateMeta,
    NgffWellMeta,
    Plate,
    RowInPlate,
    Well,
    WellInPlate,
)

from lif_converters.bioio_image_utils import scene_plate_iterate


def column_formatting(column: int | str) -> str:
    """Standard formatting for column names"""
    if isinstance(column, str):
        column = int(column)
    return f"{column:02d}"


def build_well_path(row: str, column: int | str) -> str:
    """Setup the path to the well"""
    return f"{row}/{column_formatting(column)}"


def build_acquisition_path(row: str, column: int | str, acquisition: int | str) -> str:
    """Setup the path to the acquisition"""
    return f"{build_well_path(row, column)}/{acquisition}"


def generate_plate_lists(
    image: BioImage,
) -> tuple[list[RowInPlate], list[ColumnInPlate], list[AcquisitionInPlate]]:
    """Generate the lists of rows, columns and acquisitions in the plate"""
    rows, columns, acquisitions = set(), set(), set()
    for scene in scene_plate_iterate(image):
        rows.add(scene.row)
        columns.add(scene.column)
        acquisitions.add((scene.tile_name, scene.acquisition_id))

    rows = [RowInPlate(name=row) for row in sorted(rows)]
    columns = [
        ColumnInPlate(name=column_formatting(column)) for column in sorted(columns)
    ]

    acquisitions = [
        AcquisitionInPlate(name=acquisition_name, id=acquisition_id)
        for acquisition_name, acquisition_id in acquisitions
    ]

    return rows, columns, acquisitions


def _find_row_col_idx(scene, list_rows, list_columns):
    for i, row in enumerate(list_rows):
        if row.name == scene.row:
            row_id = i
            break
    else:
        raise ValueError(f"Row {scene.row} not found in list_rows")

    for i, column in enumerate(list_columns):
        if column.name == column_formatting(scene.column):
            column_id = i
            break
    else:
        raise ValueError(f"Column {scene.column} not found in list_columns")
    return row_id, column_id


def generate_list_wells_metadata(image: BioImage, list_rows, list_columns):
    """Generate the metadata for the wells in the plate metadata."""
    wells = {}

    for scene in scene_plate_iterate(image):
        path = build_well_path(scene.row, scene.column)
        row_id, column_id = _find_row_col_idx(scene, list_rows, list_columns)
        well = WellInPlate(
            path=path,
            rowIndex=row_id,
            columnIndex=column_id,
        )
        if path not in wells:
            wells[path] = well

    wells = list(wells.values())
    return wells


def generate_plate_metadata(image: BioImage) -> NgffPlateMeta:
    """Generate the metadata for the plate."""
    list_rows, list_columns, list_acquisitions = generate_plate_lists(image)
    list_wells = generate_list_wells_metadata(image, list_rows, list_columns)
    plate_meta = Plate(
        rows=list_rows,
        columns=list_columns,
        acquisitions=list_acquisitions,
        wells=list_wells,
        version=__OME_NGFF_VERSION__,
    )
    return NgffPlateMeta(plate=plate_meta)


def generate_wells_metadata(image: BioImage) -> dict[str, Well]:
    """Generate the metadata for the wells in the plate metadata."""
    wells_meta = {}
    for scene in scene_plate_iterate(image):
        path = build_well_path(scene.row, scene.column)
        image = ImageInWell(path=str(scene.acquisition_id))
        if path not in wells_meta:
            wells_meta[path] = []
        wells_meta[path].append(image)

    wells_meta = {
        path: NgffWellMeta(well=Well(images=images, version=__OME_NGFF_VERSION__))
        for path, images in wells_meta.items()
    }
    return wells_meta
