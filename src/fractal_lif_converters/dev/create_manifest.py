"""Generate JSON schemas for task arguments afresh, and write them
to the package manifest.
"""

from fractal_tasks_core.dev.create_manifest import create_manifest

custom_pydantic_models = [
    ("fractal_lif_converters", "convert_lif_plate_init_task.py", "LifPlateInputModel"),
    (
        "fractal_lif_converters",
        "convert_lif_single_acq_init_task.py",
        "LifSingleAcqInputModel",
    ),
    ("fractal_lif_converters", "convert_lif_plate_init_task.py", "AdvancedOptions"),
]


if __name__ == "__main__":
    PACKAGE = "fractal_lif_converters"
    AUTHORS = "Lorenzo Cerrone"
    docs_link = "https://github.com/fractal-analytics-platform/fractal-lif-converters"
    create_manifest(
        package=PACKAGE,
        authors=AUTHORS,
        docs_link=docs_link,
        custom_pydantic_models=custom_pydantic_models,
    )
