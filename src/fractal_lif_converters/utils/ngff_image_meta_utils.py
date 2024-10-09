"""Utilities to generate OME-NGFF image metadata from bioio.BioImage."""

import numpy as np
from bioio import BioImage
from fractal_tasks_core import __OME_NGFF_VERSION__
from fractal_tasks_core.channels import OmeroChannel, Window, define_omero_channels
from fractal_tasks_core.ngff.specs import (
    Axis,
    Dataset,
    Multiscale,
    ScaleCoordinateTransformation,
)


def pick_color(channel_name: str) -> str:
    """Pick a color for the channel."""
    defaults = {
        "dapi": "0000FF",
        "hoechst": "0000FF",
        "gfp": "00FF00",
        "cy3": "FFFF00",
        "cy5": "FF0000",
        "brightfield": "808080",
        "red": "FF0000",
        "yellow": "FFFF00",
        "magenta": "FF00FF",
        "cyan": "00FFFF",
        "gray": "808080",
        "green": "00FF00",
    }

    def random_color():
        # TODO to be implemented
        return defaults.get("gray")

    color = defaults.get(channel_name.lower(), None)
    color = random_color() if color is None else color
    return color


def generate_omero_metadata(img_bio: BioImage) -> dict:
    """Create the Omero metadata for a BioImage object.

    Args:
        img_bio (BioImage): BioImage object to extract metadata

    Returns:
        dict: Omero metadata as a dictionary
    """
    type_info = np.iinfo(img_bio.dtype)
    omero_channels = []
    for i, channel_name in enumerate(img_bio.channel_names):
        # TODO improve the channel name (seems wrong in the example data)
        # TODO improve wavelength_id
        label = f"Ch{i + 1}"
        omero_channels.append(
            OmeroChannel(
                wavelength_id=label,
                index=i,
                label=label,
                window=Window(start=type_info.min, end=type_info.max),
                color=pick_color(channel_name),
                active=True,
            )
        )

    channels = define_omero_channels(channels=omero_channels, bit_depth=type_info.bits)
    omero = {"channels": channels, "version": __OME_NGFF_VERSION__}
    return omero


def generate_multiscale_metadata(
    img_bio: BioImage, num_levels: int = 5, coarsening_xy: int | float = 2.0
) -> Multiscale:
    """Create the multiscale metadata for a BioImage object.

    Args:
        img_bio (BioImage): BioImage object to extract metadata
        num_levels (int): Number of resolution levels
        coarsening_xy (int | float): Scaling factor for the xy axes

    Returns:
        Multiscale: Multiscale metadata
    """
    # create axes metadata
    axes = []
    scale = []

    # Create time axis if the image has multiple timepoints
    if img_bio.dims.T > 1:
        # TODO axis units are not exposed in bioio
        axes.append(Axis(name="t", type="time", unit="seconds"))
        scale.append(1.0)

    axes.append(Axis(name="c", type="channel"))
    scale.append(1.0)

    for n in ["z", "y", "x"]:
        # TODO bioio does not handle the units of the axes
        axes.append(Axis(name=n, type="space", unit="micrometer"))
        s = getattr(img_bio.physical_pixel_sizes, n.upper(), None)
        if s is None:
            s = 1.0
            # TODO add a log warning
        scale.append(s)

    # create dataset metadata for each resolution level
    list_datasets = []

    for i in range(num_levels):
        scale_transform = ScaleCoordinateTransformation(type="scale", scale=scale)
        dataset = Dataset(path=f"{i}", coordinateTransformations=[scale_transform])
        list_datasets.append(dataset)
        scale[-1] *= coarsening_xy
        scale[-2] *= coarsening_xy

    multiscale = Multiscale(
        axes=axes, datasets=list_datasets, version=__OME_NGFF_VERSION__
    )
    return multiscale


def generate_ngff_metadata(
    img_bio: BioImage, num_levels: int = 5, coarsening_xy: int | float = 2.0
) -> dict:
    """Create the NGFF metadata for a BioImage object.

    Args:
        img_bio (BioImage): BioImage object to extract metadata
        num_levels (int): Number of resolution levels
        coarsening_xy (int | float): Scaling factor for the xy axes

    Returns:
        NgffImageMeta: NGFF metadata
    """
    multiscale = generate_multiscale_metadata(
        img_bio, num_levels=num_levels, coarsening_xy=coarsening_xy
    )

    omero = generate_omero_metadata(img_bio)
    ngff = {"multiscales": [multiscale.model_dump(exclude_none=True)], "omero": omero}
    return ngff
