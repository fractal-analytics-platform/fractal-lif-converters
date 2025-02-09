### Purpose

- Convert a Leica LIF plate to a OME-Zarr Plate.

### Outputs

- A OME-Zarr Plate.

### Limitations

- This task has been tested on a limited set of acquisitions. It may not work on all Leica LIF acquisitions.
- This converter is does not support images exported in auto-saved mode.

### Expected inputs

The following plate layout are supported:

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

* Mosaique Plates

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

The names in curly braces `{}` can be freely chosen by the user. 

While the othe names must follow the following format:

* The well name must be a singe or duble letter followed by a positive integer.
Valid examples are `A1`, `A2`, `B1`, `AA1`, `AA12` etc.
* Alternatively, the well can be hierarchically structured, for example `A/1`, `A/2`, `B/1`, `AA/1`, `AA/12` etc.
* If the well is a multi-position well, the positions must be named `R` followed by a positive integer. Valid examples are `R1`, `R2`, `R3`, `R12` etc.
* In case of more complex plate formats, for example FLIM  data, the converter will ignore the data that does not follow the above formats. For example:

  ```text
  /{Project.lif}
  ----/{Tilescan 1}/
  --------/A/1/R1 (Converted)
  --------/A/1/R1/FLIM/Intensity (Ignored)
  --------------------/Fast Flim (Ignored)
  --------------------/Standard Deviation (Ignored)
  ```

