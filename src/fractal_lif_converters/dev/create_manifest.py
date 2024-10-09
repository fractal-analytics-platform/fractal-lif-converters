"""Generate JSON schemas for task arguments."""

from fractal_tasks_core.dev.create_manifest import create_manifest

if __name__ == "__main__":
    PACKAGE = "fractal_lif_converters"
    create_manifest(package=PACKAGE)
