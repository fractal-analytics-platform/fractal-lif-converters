# Fractal LIF Converters

Fractal LIF Converters is a collection of [Fractal](https://fractal-analytics-platform.github.io/) tasks that convert Leica LIF microscopy files into [OME-Zarr](https://ngff.openmicroscopy.org/) format.

## Supported Tasks

| Task | Output | Description |
|---|---|---|
| `Convert LIF Plate to OME-Zarr` | OME-Zarr HCS Plate | Converts a multi-well plate acquisition stored in a LIF file |
| `Convert LIF Image to OME-Zarr` | OME-Zarr Image | Converts one or more images from a LIF file into standalone OME-Zarr images |

Each converter reads the native Leica metadata embedded in the LIF file and produces a well-structured OME-Zarr dataset that can be viewed in tools like [napari](https://napari.org/) or processed with downstream Fractal tasks.

## Installation

```bash
pip install fractal-lif-converters
```

## How It Works

Each converter is implemented as a Fractal Compound Task that consists of two steps:

1. **Init task** — Parses the LIF metadata, creates the OME-Zarr structure, and generates a parallelization list.
2. **Compute task** — Reads the raw image tiles and writes them into the OME-Zarr dataset. This task runs in parallel across wells or scenes.

You configure the init task with one or more **acquisitions** (paths to your LIF files) and the converter handles the rest.

!!! tip "Condition Tables"
    You can attach experimental metadata (drug treatments, concentrations, replicates, etc.) to wells using a **condition table** CSV file. See the [Condition Tables](condition_tables.md) guide for details.

## Part of the OME-Zarr converters ecosystem

This converter is a thin, format-specific layer built on
[`ome-zarr-converters-tools`](https://github.com/BioVisionCenter/ome-zarr-converters-tools),
the shared engine that handles tiling, image registration, and OME-Zarr writing for
the whole Fractal converter family. Because they all share that engine, every
converter offers the same options, behavior, and development workflow.

Sibling converters built on the same tooling:

- [`fractal-czi-converters`](https://fractal-analytics-platform.github.io/fractal-czi-converters/) — Zeiss `.czi`
- [`fractal-nd2-converters`](https://fractal-analytics-platform.github.io/fractal-nd2-converters/) — Nikon `.nd2`
- [`fractal-uzh-converters`](https://fractal-analytics-platform.github.io/fractal-uzh-converters/) — HCS plates (Operetta, ScanR, CQ3K, CellVoyager, ImageXpress, custom TIFF)

## Quick Links

- [Converters overview](converters/index.md) — Common parameters and per-task guides
- [Condition Tables](condition_tables.md) — How to associate experimental metadata with wells
- [Fractal Analytics Platform](https://fractal-analytics-platform.github.io/) — The task runner used to execute these converters
