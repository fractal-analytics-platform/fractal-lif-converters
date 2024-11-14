# Lif to OME-Zarr Converters

<p align="center">
  <img src="https://raw.githubusercontent.com/fractal-analytics-platform/fractal-logos/refs/heads/main/projects/Fractal_lif_converters.png" alt="Fractal lif converter logo" width="400">
</p>

[![CI (build and test)](https://github.com/fractal-analytics-platform/fractal-lif-converters/actions/workflows/build_and_test.yml/badge.svg)](https://github.com/fractal-analytics-platform/fractal-lif-converters/actions/workflows/build_and_test.yml)
[![codecov](https://codecov.io/gh/fractal-analytics-platform/fractal-lif-converters/graph/badge.svg?token=YTN1VbbTeq)](https://codecov.io/gh/fractal-analytics-platform/fractal-lif-converters)

This repository contains the code to convert Lif files to OME-Zarr format.

## Installation

To install the package, run the following command:

```bash
pip install git+https://github.com/fractal-analytics-platform/fractal-lif-converters
```

## Example usage

* Plate Converter:

```python
from pathlib import Path

from lif_converters.wrappers import convert_lif_plate_to_omezarr

zarr_dir = "./exports" # Directory path where the OME-Zarr file will be saved
lif_file_path = "./testData_Leica/" # File or directory path containing the lif files
n_levels = 5 # Number of levels to be created in the OME-Zarr file
coarsening_xy = 2 # Coarsening factor for the xy dimensions

convert_lif_plate_to_omezarr(
    zarr_dir=zarr_dir,
    lif_files_path=lif_file_path,
    num_levels=n_levels,
    coarsening_xy=coarsening_xy,
    overwrite=True,
    verbose=True,
)
```

Where the `.lif` file is formatted as follows:

```text
/Project.lif
----/Tilescan 1/A/1
----/Tilescan 1/A/2
    ...
----/Tilescan 1/B/1
    ...
----/Tilescan 2/A/1
```

and the OME-Zarr file will be formatted as follows:

```text
/Project.zarr
----/A
--------/1
------------/0 # This will correspond to "Tilescan 1/A/1"
------------/1 # This will correspond to "Tilescan 2
            ...
```

* Single Acquisition Converter:

```python
from pathlib import Path

from lif_converters.wrappers import convert_lif_scene_to_omezarr

zarr_dir = "./exports" # Directory path where the OME-Zarr file will be saved
lif_file_path = "./testData_Leica/" # File or directory path containing the lif files
scene_name = "Scene-1" # Name of the scene to be converted
n_levels = 5 # Number of levels to be created in the OME-Zarr file
coarsening_xy = 2 # Coarsening factor for the xy dimensions

convert_lif_plate_to_omezarr(
    zarr_dir=zarr_dir,
    lif_files_path=lif_file_path,
    num_levels=n_levels,
    scene_name=scene_name,
    coarsening_xy=coarsening_xy,
    overwrite=True,
    verbose=True,
)
```

Note that the if the `scene_name` is not provided, all the scenes in the lif file will be converted in a
single Ngff Image.
