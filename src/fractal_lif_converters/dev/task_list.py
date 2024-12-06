"""Contains the list of tasks available to fractal."""

from fractal_tasks_core.dev.task_models import CompoundTask

TASK_LIST = [
    CompoundTask(
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
    ),
    CompoundTask(
        name="Convert Lif Scene to OME-Zarr",
        executable_init="convert_lif_scene_init_task.py",
        executable="convert_lif_compute_task.py",
        meta_init={"cpus_per_task": 1, "mem": 4000},
        meta={"cpus_per_task": 1, "mem": 12000},
        category="Conversion",
        tags=[
            "Leica",
            "Single Image Converter",
        ],
    ),
]
