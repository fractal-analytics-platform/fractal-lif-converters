# Changelog

## [Unreleased]

### API Breaking Changes
- Adopt `ome-zarr-converters-tools>=1.0.0,<2.0.0` (was `>=0.10.4,<0.11.0`).
- **Default table backend changed from `anndata` to `csv`.** The conversion tasks ship
  `ConverterOptions()` with v1 defaults, so the well/image table format written by real
  conversions is now CSV. Pipelines that consumed the previous AnnData tables must be
  updated (or set the table backend explicitly).

### Fix
- Disable `reindex_channels` (new v1 default `True`) in the shipped converter options.
  LIF builds multi-channel tiles (`length_c == number of channels`), but
  `reindex_channels` assumes one channel per tile and raised
  `ValueError: reindex_channels requires single-channel tiles` at compute time for every
  multi-channel image. LIF channel indices are already dense, so reindexing is
  unnecessary.

### Chores
- Migrate to the v1 `ome-zarr-converters-tools` API:
  - `AcquisitionDetails(pixelsize=...)` → `xy_pixel_size=...`; the coordinate-system
    fields `start_/length_{x,y,z,t}_coo` → `..._space` (values unchanged) in both parsers.
  - Import `ImageLoaderInterface` and `BackendType` from the package root instead of
    private submodules.
  - Regenerate `__FRACTAL_MANIFEST__.json` for the v1 schema (grouping/tiling split,
    `align_*` → `remove_*`/`remove_xy_jitter`/`reindex_channels`, scheduler `type` → `mode`,
    `csv` table-backend default).
- Note: the new `remove_xy_jitter` default (`True`) is a no-op for LIF (one tile per FOV);
  existing snapshots are unchanged (shipped test datasets are single-position, so the v1
  region-origin/pixel-grid mosaic fixes do not alter their output).

## [0.7.1]

### Fix
- Fix typos in the plate/image task docs and the `_string_validation` docstring (`single`/`double` letter, `other`) and in the conversion log message (`Successfully`); regenerate `__FRACTAL_MANIFEST__.json`.

### Chores
- Align repository tooling with `ome-zarr-converters-tools`: adopt its `.pre-commit-config.yaml` (`validate-pyproject` v0.25, `crate-ci/typos`, `astral-sh/ruff-pre-commit` v0.15.17, `nbstripout`) with a per-repo `_typos.toml`, add a `chores` pixi task, bump GitHub Actions pins (`checkout` v7, `codecov-action` v7, `action-gh-release` v3, `setup-python` v6), and add a terse `CLAUDE.md`.

## [0.7.0]

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
