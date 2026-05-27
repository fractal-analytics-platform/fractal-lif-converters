# LIF Single Acquisition

Converts one or more scenes from a Leica LIF file into standalone OME-Zarr images (not a plate structure).

## Expected File Structure

The converter expects a `.lif` file where each scene to convert is a named entry at the top level or nested one level deep. Three image layouts are supported:

=== "Single Position"

    A single image directly under the scan name:

    ```
    Project.lif
    └── Tilescan 1  (Simple Image)
    ```

=== "Multi-Position"

    Multiple positions under a scan, named `Position 1`, `Position 2`, etc.:

    ```
    Project.lif
    └── Tilescan 1/
        ├── Position 1  (Simple Image)
        ├── Position 2  (Simple Image)
        └── ...
    ```

=== "Mosaic"

    A single mosaic (tiled) image under the scan name:

    ```
    Project.lif
    └── Tilescan 1  (Mosaic Image)
    ```

Names in curly braces (e.g., `Tilescan 1`) can be freely chosen. Scans that do not match any of the supported layouts are ignored automatically.

## Naming Conventions

**Position names** (multi-position images) must be `Position` followed by a space and a positive integer:

- Valid: `Position 1`, `Position 2`, `Position 12`

## Metadata

The converter extracts the following from the LIF file:

- Scene name and stage positions (X, Y, Z)
- Channel names and IDs
- Pixel size (XY and Z spacing in micrometers)
- Timepoint indices
- Mosaic tile layout (for mosaic images)

## Task Parameters

| Field | Type | Default | Description |
|---|---|---|---|
| `Path` | `str` | *required* | Path to the `.lif` file. |
| `Tile Scan Name` | `str` or `null` | `null` | Name of the scan to convert. If `null`, all compatible scans in the file are converted (wildcard mode). |
| `Zarr Name` | `str` or `null` | `null` | Custom name for the output OME-Zarr image. Defaults to the scan name. |
| `Advanced` | `LifAcquisitionOptions` | `{}` | Advanced options: stage corrections, filters, and LIF-specific settings. See [Converters Overview](index.md). |

!!! warning "Limitations"
    - This converter has been tested on a limited set of LIF acquisitions and may not handle all formats.
    - Images exported in Leica auto-saved mode are not supported.
