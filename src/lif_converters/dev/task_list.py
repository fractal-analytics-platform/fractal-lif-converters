"""Contains the list of tasks available to fractal."""

from fractal_tasks_core.dev.task_models import NonParallelTask

TASK_LIST = [
    NonParallelTask(
        name="Lif Converter Task",
        executable="lif_converter_task.py",
        meta={"cpus_per_task": 1, "mem": 4000},
    ),
]
