"""Contains the list of tasks available to fractal."""

from fractal_task_tools.task_models import ConverterCompoundTask

AUTHORS = "Fractal Core Team"
DOCS_LINK = "https://github.com/fractal-analytics-platform/fractal-lif-converters"

INPUT_MODELS = [
    ("fractal_lif_converters", "convert_lif_plate_init_task.py", "LifPlateInputModel"),
    (
        "fractal_lif_converters",
        "convert_lif_single_acq_init_task.py",
        "LifSingleAcqInputModel",
    ),
    ("fractal_lif_converters", "convert_lif_plate_init_task.py", "AdvancedOptions"),
]


TASK_LIST = [
    ConverterCompoundTask(
        name="Convert Lif Plate to OME-Zarr",
        executable_init="convert_lif_plate_init_task.py",
        executable="convert_lif_compute_task.py",
        meta_init={"cpus_per_task": 1, "mem": 4000},
        meta={"cpus_per_task": 1, "mem": 12000},
        category="Conversion",
        modality="HCS",
        tags=[
            "Leica",
            "Plate converter",
        ],
        docs_info="file:docs_info/lif_plate_task.md",
    ),
    ConverterCompoundTask(
        name="Convert Lif Scene to OME-Zarr",
        executable_init="convert_lif_single_acq_init_task.py",
        executable="convert_lif_compute_task.py",
        meta_init={"cpus_per_task": 1, "mem": 4000},
        meta={"cpus_per_task": 1, "mem": 12000},
        category="Conversion",
        tags=[
            "Leica",
            "Single Image Converter",
        ],
        docs_info="file:docs_info/lif_single_acq_task.md",
    ),
]
