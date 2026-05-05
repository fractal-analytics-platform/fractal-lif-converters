"""Contains the list of tasks available to fractal."""

from fractal_task_tools.task_models import ConverterCompoundTask

AUTHORS = "Lorenzo Cerrone"
DOCS_LINK = "https://github.com/fractal-analytics-platform/fractal-lif-converters"


TASK_LIST = [
    ConverterCompoundTask(
        name="Convert Lif Plate to OME-Zarr",
        executable_init="lif/plate/convert_lif_plate_init_task.py",
        executable="common/image_in_plate_compute_task.py",
        meta_init={"cpus_per_task": 1, "mem": 4000},
        meta={"cpus_per_task": 1, "mem": 12000},
        category="Conversion",
        modality="HCS",
        tags=["Leica", "Plate converter"],
        docs_info="file:docs_info/lif_plate_task.md",
    ),
    ConverterCompoundTask(
        name="Convert Lif Scene to OME-Zarr",
        executable_init="lif/single/convert_lif_single_acq_init_task.py",
        executable="common/single_image_compute_task.py",
        meta_init={"cpus_per_task": 1, "mem": 4000},
        meta={"cpus_per_task": 1, "mem": 12000},
        category="Conversion",
        tags=["Leica", "Single Image Converter"],
        docs_info="file:docs_info/lif_single_acq_task.md",
    ),
]
