# How to Run the Converters

The converters in this package can be used in two ways:

- **As Fractal tasks** — configured and executed via the [Fractal Analytics Platform](https://fractal-analytics-platform.github.io/) web interface or API.
- **As Python functions** — called directly from your own scripts or Jupyter notebooks.

Both modes accept the same parameters; the Python API is a thin wrapper around the same underlying logic as the Fractal tasks.

## Running via Python API

You can also run any converter as a plain Python function. This is useful for scripting, local testing, or integrating the conversion into your own pipelines.

### Installation

```bash
pip install fractal-lif-converters
```

### Import Pattern

```python
from fractal_lif_converters import convert_lif_plate, convert_lif_image
```

All converters and acquisition models are exported from the top-level package:

```python
from fractal_lif_converters import (
    # Converters
    convert_lif_plate,
    convert_lif_image,
    # Acquisition models
    LifPlateAcquisitionModel,
    LifImageAcquisitionModel,
)
```

### Example (LIF Plate)

```python
from fractal_lif_converters import convert_lif_plate, LifPlateAcquisitionModel

acquisitions = [
    LifPlateAcquisitionModel(
        path="/path/to/plate.lif",
        plate_name="my_plate",
        acquisition_id=0,
    )
]

images = convert_lif_plate(
    zarr_dir="/output/zarr",
    acquisitions=acquisitions,
)
```

### Example (LIF Image)

```python
from fractal_lif_converters import convert_lif_image, LifImageAcquisitionModel

acquisitions = [
    LifImageAcquisitionModel(
        path="/path/to/image.lif",
    )
]

images = convert_lif_image(
    zarr_dir="/output/zarr",
    acquisitions=acquisitions,
)
```

Unlike `convert_lif_plate`, where `zarr_dir` holds one or more OME-Zarr HCS plates,
`convert_lif_image` writes each converted image as its own standalone OME-Zarr
container directly inside `zarr_dir`.

Both functions return a list of `ImageListUpdateDict` objects describing the converted OME-Zarr images.

### Common Parameters

Both functions share the same signature:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `zarr_dir` | `str` | *required* | Output directory where the OME-Zarr data will be written. |
| `acquisitions` | `list[<Model>]` | *required* | List of acquisition objects. Type varies by converter — see each converter page. |
| `converter_options` | `ConverterOptions \| None` | `None` | Advanced options (tiling, writer mode, chunking, OME-Zarr format). `None` uses the defaults. |
| `overwrite` | `OverwriteMode` | `NO_OVERWRITE` | What to do if the output already exists. |
| `runner` | `RunnerType \| None` | `None` | Execution strategy. `None` runs items sequentially. |

### Multiple Acquisitions

Pass multiple acquisition objects to convert them all into a single run. To combine them into one plate (e.g. for multiplexed experiments), use the same `plate_name` with different `acquisition_id` values:

```python
from fractal_lif_converters import convert_lif_plate, LifPlateAcquisitionModel

acquisitions = [
    LifPlateAcquisitionModel(
        path="/data/round1.lif",
        plate_name="my_plate",
        acquisition_id=0,
    ),
    LifPlateAcquisitionModel(
        path="/data/round2.lif",
        plate_name="my_plate",
        acquisition_id=1,
    ),
]

convert_lif_plate(zarr_dir="/output/zarr", acquisitions=acquisitions)
```

### Per-Converter Examples

Each converter page includes a Python API example with the converter-specific acquisition model:

- [LIF Plate](converters/lif_plate.md#python-api)
- [LIF Image](converters/lif_image.md#python-api)
