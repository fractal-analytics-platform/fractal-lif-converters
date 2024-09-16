"""Contains the list of tasks available to fractal."""

from fractal_tasks_core.dev.task_models import CompoundTask

TASK_LIST = [
    CompoundTask(
        name="Lif Plate Converter Task",
        executable_init="lif_plate_converter_init_task.py",
        executable="lif_converter_compute_task.py",
        meta_init={"cpus_per_task": 1, "mem": 4000},
        meta={"cpus_per_task": 1, "mem": 12000},
    ),
    CompoundTask(
        name="Lif Scene Converter Task",
        executable_init="lif_scene_converter_init_task.py",
        executable="lif_converter_compute_task.py",
        meta_init={"cpus_per_task": 1, "mem": 4000},
        meta={"cpus_per_task": 1, "mem": 12000},
    ),
]
