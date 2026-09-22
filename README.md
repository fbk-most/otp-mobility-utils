# otp-mobility-utils

`otp-mobility-utils` is a Python library that collects reusable functions and components for data preparation and OpenTripPlanner (OTP) simulation configuration.

The package **does not directly execute a complete pipeline** and is not tied to a specific case study. The application scripts, runners, and notebooks that use these functions belong to separate projects.

## Installation

`otp-mobility-utils` can be installed as a dependency in any Python project using [`uv`](https://docs.astral.sh/uv/).

### Install directly from GitHub

From the root directory of the project that will use the package:

```bash
uv add git+https://github.com/fbk-most/otp-mobility-utils.git
```

This command:

- downloads the package from GitHub
- adds it to the project's dependencies
- updates `pyproject.toml`
- updates the lock file

The package can then be imported normally:

```python
from otp_mobility.otp import processor
from otp_mobility.preparation import extract_bbox_from_gtfs
```

### Development setup

To contribute to `otp-mobility-utils`, clone the repository and install its development dependencies:

```bash
git clone https://github.com/fbk-most/otp-mobility-utils.git
cd otp-mobility-utils
uv sync
```

This setup is intended for developing the package itself. Applications that only use the library should install it as a Git dependency instead.

## Package Structure

The library code is located in the `src/otp_mobility/` directory.

```text
src/
└── otp_mobility/
    ├── __init__.py
    ├── preparation/
    │   ├── add_car_restrictions.py
    │   ├── add_parkrides.py
    │   ├── extract_bbox_from_gtfs.py
    │   ├── extract_elements_outside.py
    │   ├── extract_with_pyosmium.py
    │   ├── get_bbox_from_OD.py
    │   ├── parse_filter_expression.py
    │   ├── resize_av.py
    │   ├── tags_filter_with_pyosmium.py
    │   └── verify_file_sizes.py
    ├── otp/
    │   ├── generate_config.py
    │   └── processor.py
    └── utils/
        ├── config.py
        ├── constants.py
        ├── paths.py
        └── utils.py
```

The library is organized into three main areas:

- `preparation`: functions for preparing geographic data, OSM, GTFS, and OD
- `otp`: tools for configuring and querying OpenTripPlanner
- `utils`: configurations, constants, path management, and generic functions

Replace the current section with:

## The `preparation` Module

The `preparation` module contains independent utilities for preparing and validating the input data used by OTP-based applications. It does not implement a fixed workflow: each utility can be called separately and combined with other project-specific processing steps.

The module currently includes utilities for:

- OpenStreetMap data processing
- bounding box extraction
- OSM filtering and enrichment
- parking and park-and-ride preparation
- accessibility-area processing
- file validation

### OpenStreetMap processing

#### `extract_with_pyosmium`

Provides utilities for reading and processing OSM PBF files with `pyosmium`. It can be used to inspect OSM elements and extract the data required by an application.

#### `tags_filter_with_pyosmium`

Filters OSM elements according to their tags. This is useful when an application needs to retain only specific types of roads, nodes, ways, or other OSM objects.

#### `extract_elements_outside`

Extracts OSM elements located outside a specified area or geometry. This can be used to separate the data inside a study area from the surrounding network.

### Bounding boxes

#### `extract_bbox_from_gtfs`

Computes a bounding box from the geographic data contained in a GTFS feed, such as stop locations and transit geometries.

#### `get_bbox_from_OD`

Computes a bounding box from origin-destination data. The resulting extent can be used to define the geographic area required by a downstream processing step.

The bounding-box utilities do not download or process the surrounding geographic data themselves. They only derive the extent, leaving the subsequent processing to the application using the package.

### OSM filtering and enrichment

#### `parse_filter_expression`

Parses filter expressions used to select OSM elements. It provides a reusable way to convert filter definitions into conditions that can be applied during OSM processing.

#### `add_car_restrictions`

Adds or updates information related to car-access restrictions in the geographic data. The input data, geometries, and configuration must be provided by the calling application.

#### `add_parkrides`

Adds or updates information related to parking and park-and-ride facilities. The resulting data can be used in multimodal applications involving private cars and public transport.

### Accessibility areas

#### `resize_av`

Processes accessibility-area geometries by changing their size according to the parameters provided by the calling application.

The module does not define a specific study area or set of default geometries. These must be supplied by the project using the utility.

### File validation

#### `verify_file_sizes`

Provides checks for validating the size or presence of files generated during data preparation. It can be used to detect incomplete or empty output files before they are passed to later processing steps.

### Using the preparation utilities

The utilities can be imported individually:

```python
from otp_mobility.preparation import extract_bbox_from_gtfs
from otp_mobility.preparation import tags_filter_with_pyosmium
from otp_mobility.preparation import verify_file_sizes
```

The application using these utilities is responsible for:

- providing input files and geometries
- defining configuration parameters
- deciding the order in which utilities are executed
- managing temporary and output files
- handling errors and logging
- integrating the results into its own workflow

## The `otp` Module

The `otp` module contains tools specific to OpenTripPlanner integration.

### `otp.generate_config`

This module generates configuration files used by OTP, including:

- static graph configuration
- references to OSM and GTFS files
- routing parameter configuration
- routing search settings

Configuration generation can be used by an external application without needing to replicate the JSON file structure required by OTP.

### `otp.processor`

This module contains the logic for executing routing requests to an OTP endpoint via GraphQL.

Features include:

- building GraphQL requests
- handling multiple origin-destination pairs
- using different transport modes
- executing batch requests
- managing routing results
- attempting alternative routes with small coordinate variations when a path is not found

The module is designed to be used by scripts or applications that independently manage:

- input loading
- scenario selection
- result saving
- postprocessing

Conceptual example:

```python
from otp_mobility.otp import processor

# Use functions from the processor module
# to build and execute requests to OTP.
```

The available functions and their respective parameters should be consulted directly in the module code or in the project's API documentation.


## The `utils` Module

The `utils` module contains cross-cutting components used by other submodules and external applications.

### `utils.config`

Manages shared configurations and parameters, avoiding duplication of values and settings across different scripts using the package.

### `utils.constants`

Collects reusable constants, such as names, default values, and identifiers used in data preparation or OTP requests.

### `utils.paths`

Centralizes the construction and management of file paths.

## Usage in Another Project

After installation, the package can be imported normally:

```python
from otp_mobility import otp
from otp_mobility import preparation
from otp_mobility import utils
```

It is also possible to import individual modules directly:

```python
from otp_mobility.preparation import get_bbox_from_OD
from otp_mobility.preparation import tags_filter_with_pyosmium
from otp_mobility.otp import generate_config
```

The application using the package must handle:

- locating input files
- defining output paths
- providing scenario-specific configurations
- orchestrating different functions
- managing logging, errors, and results
- optionally starting OTP

## Development

To set up the development environment:

```bash
uv venv
uv sync
```

To verify that the package is importable:

```bash
uv run python -c "import otp_mobility; print(otp_mobility)"
```

Tests and scripts using the package should be run from the project's main directory, maintaining consistent configuration and dependencies.