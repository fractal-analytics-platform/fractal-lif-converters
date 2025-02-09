### Purpose

- Convert a Leica LIF acquisition to a OME-Zarr Image.

### Outputs

- A OME-Zarr Image.

### Limitations

- This task has been tested on a limited set of acquisitions. It may not work on all Leica LIF acquisitions.
- This converter is does not support images exported in auto-saved mode.

### Expected inputs

The following image layout are supported:

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

* Mosaique Image
  
    ```text
    /{Project.lif}
    ----/{Tilescan 1} (Mosaic Image)
    ```


The names in curly braces `{}` can be freely chosen by the user. While
the othe names must follow the following format:

If the scene is a multi-position image, the positions must be named `Position` followed by a space and a positive integer. Valid examples are `Position 1`, `Position 2`, `Position 3`, `Position 12` etc.

Moreover, if the lif file contains scans that do not follow the above formats, the converter will ignore them.
