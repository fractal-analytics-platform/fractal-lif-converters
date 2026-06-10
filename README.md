# Fractal LIF Converters

[![CI (build and test)](https://github.com/fractal-analytics-platform/fractal-lif-converters/actions/workflows/build_and_test.yml/badge.svg)](https://github.com/fractal-analytics-platform/fractal-lif-converters/actions/workflows/build_and_test.yml)
[![codecov](https://codecov.io/gh/fractal-analytics-platform/fractal-lif-converters/graph/badge.svg?token=YTN1VbbTeq)](https://codecov.io/gh/fractal-analytics-platform/fractal-lif-converters)

A collection of [Fractal](https://fractal-analytics-platform.github.io/) tasks
to convert Leica `.lif` files into [OME-Zarr](https://ngff.openmicroscopy.org/)
format.

## Tasks

| Task | Use case |
|---|---|
| `Convert Lif Plate to OME-Zarr` | Convert a `.lif` containing a plate-shaped tile-scan into an OME-Zarr HCS plate. |
| `Convert Lif Image to OME-Zarr` | Convert a single image (single-position, multi-position, or mosaic) into a standalone OME-Zarr image. |

Each task is a Fractal **compound task**: an init step parses the `.lif`
metadata and builds the parallelization list, and a compute step writes the
image data well-by-well (or scene-by-scene).

## Installation

```bash
pip install fractal-lif-converters
```

## Part of the Fractal OME-Zarr converters ecosystem

This converter is a thin, format-specific layer built on
[`ome-zarr-converters-tools`](https://github.com/BioVisionCenter/ome-zarr-converters-tools),
the shared engine that handles tiling, image registration, and OME-Zarr writing for
the whole Fractal converter family. Because they all share that engine, every
converter offers the same options, behavior, and development workflow.

Sibling converters built on the same tooling:

- [`fractal-czi-converters`](https://github.com/fractal-analytics-platform/fractal-czi-converters) — Zeiss `.czi`
- [`fractal-nd2-converters`](https://github.com/fractal-analytics-platform/fractal-nd2-converters) — Nikon `.nd2`
- [`fractal-uzh-converters`](https://github.com/fractal-analytics-platform/fractal-uzh-converters) — HCS plates (Operetta, ScanR, CQ3K, CellVoyager, ImageXpress, custom TIFF)

## Documentation

Full documentation — including the supported file layouts, all converter
parameters, and the condition-table format — is available at
<https://fractal-analytics-platform.github.io/fractal-lif-converters/>.
