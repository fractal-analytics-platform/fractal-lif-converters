# LIF Plate

Converts a Leica LIF file containing a multi-well plate acquisition into an OME-Zarr HCS plate.

## Expected File Structure

The converter expects a `.lif` file where plate wells are organized under a named tile scan. Three plate layouts are supported:

=== "Single Position"

    One image per well, using flat well names (`A1`) or hierarchical well names (`A/1`):

    ```
    Project.lif
    └── Tilescan 1/
        ├── A1  (Simple Image)
        ├── B1  (Simple Image)
        └── ...
    ```

    ```
    Project.lif
    └── Tilescan 1/
        └── A/
            └── 1  (Simple Image)
    ```

=== "Multi-Position"

    Multiple positions per well, named `R1`, `R2`, etc.:

    ```
    Project.lif
    └── Tilescan 1/
        ├── A1/
        │   ├── R1  (Simple Image)
        │   ├── R2  (Simple Image)
        │   └── ...
        └── ...
    ```

    ```
    Project.lif
    └── Tilescan 1/
        └── A/
            └── 1/
                ├── R1  (Simple Image)
                ├── R2  (Simple Image)
                └── ...
    ```

=== "Mosaic"

    One mosaic (tiled) image per well:

    ```
    Project.lif
    └── Tilescan 1/
        ├── A1  (Mosaic Image)
        ├── B1  (Mosaic Image)
        └── ...
    ```

    ```
    Project.lif
    └── Tilescan 1/
        └── A/
            ├── 1  (Mosaic Image)
            └── ...
    ```

Names in curly braces (e.g., `Tilescan 1`) can be freely chosen. All other names must follow the conventions below.

## Naming Conventions

**Well names** must be one or two letters followed by a positive integer:

- Valid: `A1`, `B2`, `AA1`, `AA12`
- Or hierarchical: `A/1`, `A/2`, `AA/1`

**Position names** (multi-position wells) must be `R` followed by a positive integer:

- Valid: `R1`, `R2`, `R12`

!!! info "Complex plate formats"
    If the LIF file contains additional sub-images (e.g., FLIM intensity maps), the converter ignores any entries that do not match the expected naming formats:

    ```
    Project.lif
    └── Tilescan 1/
        └── A/
            └── 1/
                ├── R1          ← converted
                └── R1/
                    └── FLIM/
                        ├── Intensity      ← ignored
                        └── Fast Flim      ← ignored
    ```

## Metadata

The converter extracts the following from the LIF file:

- Well position (row and column)
- Field-of-view index and stage positions (X, Y, Z)
- Channel names and IDs
- Pixel size (XY and Z spacing in micrometers)
- Timepoint indices
- Mosaic tile layout (for mosaic images)

## Task Parameters

| Field | Type | Default | Description |
|---|---|---|---|
| `Path` | `str` | *required* | Path to the `.lif` file. |
| `Tile Scan Name` | `str` or `null` | `null` | Name of the tile scan to convert. If `null`, all tile scans in the file are converted (wildcard mode). |
| `Plate Name` | `str` or `null` | `null` | Custom name for the output OME-Zarr plate. Defaults to the LIF file name. |
| `Acquisition Id` | `int` | `0` | Acquisition identifier for combining multiple acquisitions into a single plate. |
| `Advanced` | `LifAcquisitionOptions` | `{}` | Advanced options: condition table, stage corrections, filters, and LIF-specific settings. See [Converters Overview](index.md). |

!!! warning "Limitations"
    - This converter has been tested on a limited set of LIF acquisitions and may not handle all formats.
    - Images exported in Leica auto-saved mode are not supported.

## Python API

```python
from fractal_lif_converters import convert_lif_plate, LifPlateAcquisitionModel

acquisitions = [
    LifPlateAcquisitionModel(
        path="/path/to/plate.lif",
        plate_name="my_plate",
        acquisition_id=0,
    )
]

convert_lif_plate(
    zarr_dir="/output/zarr",
    acquisitions=acquisitions,
)
```

See [How to Run the Converters](../how_to_run_the_converters.md) for all common parameters and execution details.
