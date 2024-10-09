"""This task converts simple H5 files to OME-Zarr."""

from pathlib import Path
from typing import Optional

import bioio_lif
from bioio import BioImage
from fractal_tasks_core.utils import logger
from pydantic import Field, validate_call

from fractal_lif_converters.convert_lif_compute_task import ComputeInputModel


def _rename_scene(scene_name: str):
    scene_name = scene_name.replace(" ", "-")
    scene_name = scene_name.replace("/", "_")
    return scene_name


def _create_zarr_image_url(zarr_dir, lif_stem, scene_name):
    scene_name = _rename_scene(scene_name=scene_name)
    zarr_url = Path(zarr_dir) / f"{lif_stem}.zarr" / scene_name
    return str(zarr_url)


def _create_parrallelization_list_entry(
    zarr_dir,
    lif_file_path,
    scene_name,
    num_levels: int,
    coarsening_xy: float,
    overwrite: bool,
    swap_xy_axes: bool,
):
    zarr_url = _create_zarr_image_url(
        zarr_dir=zarr_dir, lif_stem=lif_file_path.stem, scene_name=scene_name
    )
    task_kwargs = {
        "zarr_url": str(zarr_url),
        "init_args": ComputeInputModel(
            lif_path=str(lif_file_path),
            scene_name=scene_name,
            num_levels=num_levels,
            coarsening_xy=coarsening_xy,
            overwrite=overwrite,
            plate_mode=False,
            swap_xy_axes=swap_xy_axes,
        ).model_dump(),
    }
    return task_kwargs


@validate_call
def convert_lif_scene_init_task(
    *,
    # Fractal parameters
    zarr_urls: list[str],
    zarr_dir: str,
    # Task parameters
    lif_files_path: str,
    scene_name: Optional[str] = None,  # noqa Fractal manifest building only supports Optional
    swap_xy_axes: bool = False,
    num_levels: int = Field(default=5, ge=0),
    coarsening_xy: int = Field(default=2, ge=1),
    overwrite: bool = False,
):
    """Initialize the conversion of LIF files to OME-Zarr - NgffImages.

    Args:
        zarr_urls (list[str]): List of zarr urls.
        zarr_dir (str): Output path to save the OME-Zarr file.
        lif_files_path (str): Input path to the LIF file,
            or a folder containing LIF files.
        scene_name (str | None): Name of the scene to convert. If None all scenes in the
            lif file will will converted. If a folder of lif files is provided, the
            scene_nane will be converted from each file.
        swap_xy_axes (bool): If True, the xy axes will be swapped. Defaults to False.
        num_levels (int): The number of resolution levels. Defaults to 5.
        coarsening_xy (float): The scaling factor for the xy axes. Defaults to 2.0.
        overwrite (bool): If True, the zarr store will be overwritten.
    """
    lif_files_path = Path(lif_files_path)
    if lif_files_path.is_dir():
        list_all_lif = list(lif_files_path.glob("*.lif"))
    elif lif_files_path.is_file():
        list_all_lif = [lif_files_path]
    else:
        raise ValueError()
    parallelization_list = []

    for lif_file_path in list_all_lif:
        img_bio = BioImage(lif_file_path, reader=bioio_lif.Reader)
        if scene_name is None:
            list_scenes = img_bio.scenes
        else:
            if scene_name in img_bio.scenes:
                list_scenes = [scene_name]
            else:
                logger.warning(f"Scene {scene_name} not found in {lif_file_path}")

        for _scene in list_scenes:
            parallelization_list.append(
                _create_parrallelization_list_entry(
                    zarr_dir=zarr_dir,
                    lif_file_path=lif_file_path,
                    scene_name=_scene,
                    num_levels=num_levels,
                    coarsening_xy=coarsening_xy,
                    overwrite=overwrite,
                    swap_xy_axes=swap_xy_axes,
                )
            )
            logger.info(
                f"{lif_file_path} - {_scene} added to the parallelization list."
            )

    logger.info(f"Found {len(parallelization_list)} scenes to convert.")
    return {"parallelization_list": parallelization_list}


if __name__ == "__main__":
    from fractal_tasks_core.tasks._utils import run_fractal_task

    run_fractal_task(task_function=convert_lif_scene_init_task)
