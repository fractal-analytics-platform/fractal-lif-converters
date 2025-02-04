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
pip install fractal-lif-converters
```

## Plate Conversion

The lif converters package provides a simple interface to convert lif files to OME-Zarr Plate format.
The package provides a high-level function `convert_lif_plate_to_omezarr` that takes a list of `LifInputModel` objects as input and converts the lif files to OME-Zarr format.

### Example Usage

* **Simple Plate Conversion**: convert a single lif scene to a OME-Zarr Plate

    ```python
    from pathlib import Path

    from lif_converters.wrappers import 
    convert_lif_plate_to_omezarr

    from lif_converters import LifInputModel

    conversion_list = [
        LifInputModel(
            lif_file_path="path/to/your.lif",
            plate_name="plate_name",
            tile_scan_name="tile_scan_name",
        )
    ]

    convert_lif_plate_to_omezarr(
        zarr_dir="path/to/exports/", # Directory path where the OME-Zarr file will be saved
        conversion_list=conversion_list,
        num_levels=5, # Number of levels to be created in the OME-Zarr file
        coarsening_xy=2, # Coarsening factor for the xy dimensions
        overwrite=True,
        verbose=True,
    )
    ```

* **Multiplexing Plate Conversion**: Convert multiple lif scenes to a single OME-Zarr plate with multiple acquisitions

    ```python
    from pathlib import Path

    from lif_converters.wrappers import 
    convert_lif_plate_to_omezarr

    from lif_converters import LifInputModel

    conversion_list = [
        LifInputModel(
            lif_file_path="path/to/your.lif",
            plate_name="plate_name",
            tile_scan_name="tile_scan_name",
            acquisition_id=0,
        ),
        LifInputModel(
            lif_file_path="path/to/your.lif", # Can be the same lif file or a different one
            plate_name="plate_name", # MUST BE THE SAME AS THE FIRST ONE
            tile_scan_name="tile_scan_name",
            acquisition_id=1, # MUST BE DIFFERENT FROM THE FIRST ONE
        )
    ]

    convert_lif_plate_to_omezarr(
        zarr_dir="path/to/exports/", # Directory path where the OME-Zarr file will be saved
        conversion_list=conversion_list,
        num_levels=5, # Number of levels to be created in the OME-Zarr file
        coarsening_xy=2, # Coarsening factor for the xy dimensions
        overwrite=True,
        verbose=True,
    )
    ```

* **Wildcard Plate Conversion**: if no `tile_scan_name` is provided, the converter will convert all tile scans in the lif file.
In this case, no `acquisition_id` or `plate_name` can be provided.

    ```python
    from pathlib import Path

    from lif_converters.wrappers import 
    convert_lif_plate_to_omezarr

    from lif_converters import LifInputModel

    conversion_list = [
        LifInputModel(
            lif_file_path="path/to/your.lif",
        )
    ]

    convert_lif_plate_to_omezarr(
        zarr_dir="path/to/exports/", # Directory path where the OME-Zarr file will be saved
        conversion_list=conversion_list,
        num_levels=5, # Number of levels to be created in the OME-Zarr file
        coarsening_xy=2, # Coarsening factor for the xy dimensions
        overwrite=True,
        verbose=True,
    )
    ```

### Supported Lif File Layouts

The following plate layout are supported:

* Single Position Plates

    ```text
    /Project.lif
    ----/Tilescan 1/
    --------/A
    ------------/1 (Simple Image)
    ```

    ```text
    /Project.lif
    ----/Tilescan 1/
    --------/A1 (Simple Image)
    --------/...
    ```

* Multi Position Plates

    ```text
    /Project.lif
    ----/Tilescan 1/
    --------/A
    ------------/1
    ----------------/R1 (Simple Image)
    ----------------/R2 (Simple Image)
    ----------------/...
    ```

    ```text
    /Project.lif
    ----/Tilescan 1/
    --------/A1
    ------------/R1 (Simple Image)
    ------------/R2 (Simple Image)
    ------------/...
    ```

* Mosaique Plates

    ```text
    /Project.lif
    ----/Tilescan 1/
    --------/A
    ------------/1 (Mosaic Image)
    ------------/...
    ```

    ```text
    /Project.lif
    ----/Tilescan 1/
    --------/A1 (Mosaic Image)
    --------/...
    ```

#### Edge cases

* In case of more complex plate formats, for example FLIM  data, the converter will ignore the data thad does not follow the above formats. For example:

  ```text
  /Project.lif
  ----/Tilescan 1/
  --------/A/1/R1 (Converted)
  --------/A/1/R1/FLIM/Intensity (Ignored)
  --------------------/Fast Flim (Ignored)
  --------------------/Standard Deviation (Ignored)
  ```

## OME-Zarr Image Conversion

The lif converters package provides a simple interface to convert lif files to OME-Zarr Image format.
The package provides a high-level function `convert_lif_image_to_omezarr` that takes a list of `LifInputModel` objects as input and
converts each element in a OME-Zarr Image.

### Example Image Conversion

* **Simple Image Conversion**: convert a single lif scene to a OME-Zarr Image

    ```python
    from pathlib import Path

    from lif_converters.wrappers import 
    convert_lif_image_to_omezarr

    from lif_converters import LifInputModel

    conversion_list = [
        LifInputModel(
            lif_file_path="path/to/your.lif",
            zarr_name="output",
            tile_scan_name="tile_scan_name", # Optional
        ),
        LifInputModel(
            lif_file_path="path/to/your.lif", # Can be the same lif file or a different one
            zarr_name="output2", # MUST BE DIFFERENT FROM THE FIRST ONE
            tile_scan_name="tile_scan_name_2", # If given, the converter will only convert the given tile scan
        )
    ]

    convert_lif_image_to_omezarr(
        zarr_dir="path/to/exports/", # Directory path where the OME-Zarr file will be saved
        conversion_list=conversion_list,
        num_levels=5, # Number of levels to be created in the OME-Zarr file
        coarsening_xy=2, # Coarsening factor for the xy dimensions
        overwrite=True,
        verbose=True,
    )
    ```

* **Wildcard Image Conversion**: if no `tile_scan_name` is provided, the converter will convert all tile scans in the lif file.
In this case, no `zarr_name` can be provided.

    ```python
    from pathlib import Path

    from lif_converters.wrappers import 
    convert_lif_image_to_omezarr

    from lif_converters import LifInputModel

    conversion_list = [
        LifInputModel(
            lif_file_path="path/to/your.lif",
        ),
    ]

    convert_lif_image_to_omezarr(
        zarr_dir="path/to/exports/", # Directory path where the OME-Zarr file will be saved
        conversion_list=conversion_list,
        num_levels=5, # Number of levels to be created in the OME-Zarr file
        coarsening_xy=2, # Coarsening factor for the xy dimensions
        overwrite=True,
        verbose=True,
    )
    ```

### Supported Lif File Layouts

The following image layout are supported:

* Single Position Image

    ```text
    /Project.lif
    ----/Tilescan 1 (Simple Image)
    ```

* Multi Position Image
  
    ```text
    /Project.lif
    ----/Tilescan 1/
    --------/Poisition 1 (Simple Image)
    --------/Poisition 2 (Simple Image)
    --------/...
    ```

* Mosaique Image
  
    ```text
    /Project.lif
    ----/Tilescan 1 (Mosaic Image)
    ```

#### Edge cases

* If the lif file contains scans that do not follow the above formats, the converter will ignore them.