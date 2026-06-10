# Lif to OME-Zarr Converters

<p align="center">
  <img src="https://raw.githubusercontent.com/fractal-analytics-platform/fractal-logos/refs/heads/main/projects/Fractal_lif_converters.png" alt="Fractal lif converter logo" width="400">
</p>

[![CI (build and test)](https://github.com/fractal-analytics-platform/fractal-lif-converters/actions/workflows/build_and_test.yml/badge.svg)](https://github.com/fractal-analytics-platform/fractal-lif-converters/actions/workflows/build_and_test.yml)
[![codecov](https://codecov.io/gh/fractal-analytics-platform/fractal-lif-converters/graph/badge.svg?token=YTN1VbbTeq)](https://codecov.io/gh/fractal-analytics-platform/fractal-lif-converters)

A collection of [Fractal](https://fractal-analytics-platform.github.io/) tasks
to convert Leica `.lif` files into [OME-Zarr](https://ngff.openmicroscopy.org/)
format.

## Tasks

| Task | Use case |
|---|---|
| `Convert Lif Plate to OME-Zarr` | Convert a `.lif` containing a plate-shaped tile-scan into an OME-Zarr HCS plate. |
| `Convert Lif Image to OME-Zarr` | Convert a single image (single-position, multi-position, or mosaic) into a standalone OME-Zarr image. |

Each task is a Fractal **compound task**: an init step parses the `.lif`
metadata and builds the parallelization list, and a compute step writes the
image data well-by-well (or scene-by-scene).

## Installation

```bash
pip install fractal-lif-converters
```

## Supported Lif File Plate Layouts

The following plate layouts are supported:

* Single Position Plates

    ```text
    /{Project.lif}
    ----/{Tilescan 1}/
    --------/A
    ------------/1 (Simple Image)
    ```

    ```text
    /{Project.lif}
    ----/{Tilescan 1}/
    --------/A1 (Simple Image)
    --------/...
    ```

* Multi Position Plates

    ```text
    /{Project.lif}
    ----/{Tilescan 1}/
    --------/A
    ------------/1
    ----------------/R1 (Simple Image)
    ----------------/R2 (Simple Image)
    ----------------/...
    ```

    ```text
    /{Project.lif}
    ----/{Tilescan 1}/
    --------/A1
    ------------/R1 (Simple Image)
    ------------/R2 (Simple Image)
    ------------/...
    ```

* Mosaic Plates

    ```text
    /{Project.lif}
    ----/{Tilescan 1}/
    --------/A
    ------------/1 (Mosaic Image)
    ------------/...
    ```

    ```text
    /{Project.lif}
    ----/{Tilescan 1}/
    --------/A1 (Mosaic Image)
    --------/...
    ```

The names in curly braces `{}` can be freely chosen by the user. The other
names must follow these conventions:

* Well names are a single or double letter followed by a positive integer.
  Valid examples: `A1`, `A2`, `B1`, `AA1`, `AA12`.
* Wells can also be hierarchically structured, e.g. `A/1`, `A/2`, `B/1`,
  `AA/1`, `AA/12`.
* Multi-position wells use `R` followed by a positive integer for each
  position: `R1`, `R2`, `R3`, `R12`.
* For more complex layouts (e.g. FLIM), the converter ignores any data that
  doesn't follow the conventions above. For example:

  ```text
  /{Project.lif}
  ----/{Tilescan 1}/
  --------/A/1/R1 (Converted)
  --------/A/1/R1/FLIM/Intensity (Ignored)
  --------------------/Fast Flim (Ignored)
  --------------------/Standard Deviation (Ignored)
  ```

## Supported Lif File Image Layouts

The following image layouts are supported:

* Single Position Image

    ```text
    /{Project.lif}
    ----/{Tilescan 1} (Simple Image)
    ```

* Multi Position Image

    ```text
    /{Project.lif}
    ----/{Tilescan 1}/
    --------/Position 1 (Simple Image)
    --------/Position 2 (Simple Image)
    --------/...
    ```

* Mosaic Image

    ```text
    /{Project.lif}
    ----/{Tilescan 1} (Mosaic Image)
    ```

The names in curly braces `{}` can be freely chosen by the user. For
multi-position images the position names must be `Position` followed by a
space and a positive integer, e.g. `Position 1`, `Position 2`, `Position 12`.
Scans that don't follow these conventions are ignored.
