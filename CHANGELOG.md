# Changelog

## [Unreleased]

### Breaking Changes
- Rename the "single acquisition" converter to "image": the Fractal task `Convert Lif Scene to OME-Zarr` is now `Convert Lif Image to OME-Zarr`, the `lif_single` package is now `lif_image`, `LifSingleAcqAcquisitionModel` is now `LifImageAcquisitionModel`, and `convert_lif_single_acq_init_task` is now `convert_lif_image_init_task`.

### Features
- Add Python API functions (`convert_lif_plate`, `convert_lif_image`) for programmatic use outside Fractal.
- Update tests to call the high-level API functions end-to-end.

### Docs
- Add "How to Run the Converters" page with Python API examples.
- Add Python API section to each converter page.

### Chores
- Rename internal modules to `_{module_name}.py` to signal private implementation (`common/_utils.py`, `common/_loaders.py`, `common/_options.py`, `common/_string_validation.py`, `common/_tile_builders.py`, `lif_plate/_parser.py`, `lif_image/_parser.py`).
- Remove `lif_image/_setup.py` (now built into `ome-zarr-converters-tools>=0.10.0`).
- Bump to `ome-zarr-converters-tools>=0.10.0,<0.11.0`.

## [0.6.0]

### Features
- Migrate from `bioformats` to `liffile` for reading LIF files, improving performance and reducing dependencies.
- Optimize memory usage in the mosaic loader.

### Bug Fixes
- Fix C/Z axis transposition in `_to_canonical_shape`.

### Chores
- Bump to latest `ome-zarr-converters-tools>=0.9.0,<0.10.0` and `ngio>=0.5.8,<0.6.0` versions.
- Add extended test datasets and improve test coverage.
- Update documentation.
- Update license.

## [0.5.0]

### Bug Fixes
- Fix broken import in `__init__.py`.
- Fix `package_name` in `__version__`.
- Fix issue #7.

### Chores
- Improve CI configuration (add Windows support).

## [0.4.0]

### Features
- Add "Convert Lif Scene to OME-Zarr" task for single-acquisition conversion.
- Improve LIF file parsing.
- Expose advanced acquisition parameters.

### Chores
- Update to `ome-zarr-converters-tools` tooling.
