"""Utilities to generate OME-NGFF image metadata from bioio.BioImage."""

import numpy as np
from bioio import BioImage
from fractal_tasks_core import __OME_NGFF_VERSION__
from fractal_tasks_core.channels import OmeroChannel, Window, define_omero_channels
from fractal_tasks_core.ngff.specs import (
    Axis,
    Dataset,
    Multiscale,
    NgffImageMeta,
    Omero,
    ScaleCoordinateTransformation,
)


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
        omero_channels.append(
            OmeroChannel(
                wavelength_id=f"C{i+1:02d}",
                index=i,
                label=channel_name,
                window=Window(start=type_info.min, end=type_info.max),
            )
        )
    channels = define_omero_channels(channels=omero_channels, bit_depth=type_info.bits)
    omero = Omero(channels=channels)
    omero = omero.model_dump(exclude_none=True)
    omero["version"] = __OME_NGFF_VERSION__
    return omero


def generate_multiscale_metadata(
    img_bio: BioImage, num_levels: int = 5, xy_scaling: float = 2.0
) -> Multiscale:
    """Create the multiscale metadata for a BioImage object.

    Args:
        img_bio (BioImage): BioImage object to extract metadata
        num_levels (int): Number of resolution levels
        xy_scaling (float): Scaling factor for the xy axes

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
        scale[-1] *= xy_scaling
        scale[-2] *= xy_scaling

    multiscale = Multiscale(
        axes=axes, datasets=list_datasets, version=__OME_NGFF_VERSION__
    )
    return multiscale


def generate_ngff_metadata(
    img_bio: BioImage, num_levels: int = 5, xy_scaling: float = 2.0
) -> NgffImageMeta:
    """Create the NGFF metadata for a BioImage object.

    Args:
        img_bio (BioImage): BioImage object to extract metadata
        n_levels (int): Number of resolution levels
        xy_scaling (float): Scaling factor for the xy axes

    Returns:
        NgffImageMeta: NGFF metadata
    """
    multiscale = generate_multiscale_metadata(
        img_bio, n_levels=num_levels, xy_scaling=xy_scaling
    )

    omero = generate_omero_metadata(img_bio)
    ngff = NgffImageMeta(multiscales=[multiscale], omero=omero)
    return ngff
