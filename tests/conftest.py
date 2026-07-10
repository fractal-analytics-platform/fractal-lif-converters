import pytest
from ome_zarr_converters_tools import (
    BackendType,
    ConverterOptions,
    OmeZarrOptions,
    StagePositionCorrections,
)

# Load the shared snapshot-testing plugin: the --update-snapshots / --extended
# options, the `extended` marker and its skip behaviour, and the
# `update_snapshots` fixture.
pytest_plugins = ["ome_zarr_converters_tools.testing.plugin"]


@pytest.fixture
def converter_options():
    # Mirror the shipped default: LIF tiles are multi-channel, so the v1 default
    # `reindex_channels=True` (which assumes one channel per tile) is incompatible.
    return ConverterOptions(
        omezarr_options=OmeZarrOptions(
            ngff_version="0.5", table_backend=BackendType.CSV
        ),
        stage_position_corrections=StagePositionCorrections(reindex_channels=False),
    )
