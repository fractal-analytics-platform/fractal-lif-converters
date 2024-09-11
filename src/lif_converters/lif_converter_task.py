"""This task converts simple H5 files to OME-Zarr."""

from pathlib import Path
from typing import Optional

from fractal_tasks_core.utils import logger
from pydantic import Field, validate_call


def convert_single_lif_to_ome_zarr(zarr_dir: str, image_path: str) -> tuple[str, str]:
    """Convert a single LIF file to OME-Zarr.

    Args:
        zarr_dir (str): Output path to save the OME-Zarr file.
        image_path (str): Input path to the LIF file.

    Returns:
        tuple[str, str]: URL to the OME-Zarr file, and layout of the image (2D or 3D).
    """
    logger.info(f"Converting LIF file {image_path} to OME-Zarr.")
    raise NotImplementedError("This function is not implemented yet.")


@validate_call
def lif_converter_task(
    zarr_urls: list[str],
    zarr_dir: str,
    image_path: str,
):
    """LIF (Leica Image File) to OME-Zarr converter task.

    Args:
        zarr_urls (list[str]): List of URLs to the OME-Zarr files.
            Not used in this task.
        zarr_dir (str): Output path to save the OME-Zarr file.
        image_path (str): Input path to the LIF file, or a folder containing LIF files.
    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise ValueError(f"Input path {image_path} does not exist.")

    if image_path.is_dir():
        files = list(image_path.glob("*.lif"))
    else:
        files = [image_path]

    image_list_updates = []
    for file in files:
        new_zarr_url, layout = convert_single_lif_to_ome_zarr(
            zarr_dir=zarr_dir,
            image_path=file,
        )

        if layout == "2D":
            is_3d = False
        else:
            is_3d = True

        image_update = {"zarr_url": new_zarr_url, "types": {"is_3D": is_3d}}
        image_list_updates.append(image_update)

    return {"image_list_updates": image_list_updates}


if __name__ == "__main__":
    from fractal_tasks_core.tasks._utils import run_fractal_task

    run_fractal_task(task_function=lif_converter_task)
