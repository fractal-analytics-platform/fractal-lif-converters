# Changelog

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
