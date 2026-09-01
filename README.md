# otp-gdb-mobility

This project prepares OD and OSM data for a Bologna mobility study and runs OpenTripPlanner (OTP) simulations to compare travel times across different transport modes and spatial contexts.

The workflow is structured around three main blocks:

- OD preparation from the municipal zoning system and the AV boundary
- OSM preprocessing for Bologna, including filtering, parking handling and access restrictions
- OTP routing simulations for local and remote environments, with batch GraphQL queries and postprocessing notebooks

## Repository structure

```text
.
├── README.md
├── main.py
├── pyproject.toml
├── uv.lock
├── data/
│   ├── input_geo/
│   │   └── area_verde_manual_v1.geojson
│   ├── input_od/
│   │   ├── Shape_zone.SHP
│   │   ├── Shape_zone_centroid.SHP
│   │   └── PROGETTO-OD.xlsx
│   ├── input_service/
│   │   ├── config_filter_rules.sh
│   │   ├── nord-est-260826.osm.pbf
│   │   └── gommagtfsbo_20250513.zip
│   └── output/
│       ├── tmp/
│       ├── build-config.json
│       ├── routing-config.json
│       ├── od-coords-extended.parquet
│       ├── od-coords-simplified.parquet
│       ├── od-coords-av.parquet
│       ├── bologna-area-filtered-parking.osm.pbf
│       ├── bologna-area-filtered-parking-inside-AV.osm.pbf
│       ├── bologna-area-filtered-parking-inside-AV-footway.osm.pbf
│       └── bologna-area-filtered-parking-outside-AV.osm.pbf
├── runners/
│   ├── config.py
│   ├── get_OD_points.py
│   ├── get_OSM_data_with_osmiumtool.sh
│   ├── get_OSM_data_with_pyosmium.py
│   ├── paths.py
│   ├── run_otp_simulation_locally.py
│   └── run_otp_simulation_remotely.ipynb
├── src/
│   └── otp_mobility/
│       ├── __init__.py
│       ├── otp/
│       │   ├── generate_config.py
│       │   └── processor.py
│       ├── preparation/
│       │   ├── add_car_restrictions.py
│       │   ├── add_parkrides.py
│       │   ├── extract_bbox_from_gtfs.py
│       │   ├── extract_elements_outside.py
│       │   ├── extract_with_pyosmium.py
│       │   ├── get_bbox_from_OD.py
│       │   ├── parse_filter_expression.py
│       │   ├── resize_av.py
│       │   ├── tags_filter_with_pyosmium.py
│       │   └── verify_file_sizes.py
│       └── utils/
│           ├── config.py
│           ├── constants.py
│           ├── paths.py
│           └── utils.py
└── notebooks/
    └── postprocessing/
        ├── check_extended_results.ipynb
        └── check_simplified_results.ipynb
```

## Python environment

This project targets Python 3.12+ and uses uv for dependency management.

```bash
uv venv
uv sync
```

Scripts are run from the repository root with the managed environment so the package under `src/otp_mobility` is correctly imported.

```bash
uv run python runners/get_OD_points.py
```

## Required input data

Before executing the pipeline, make sure the following files are available:

- `data/input_geo/area_verde_manual_v1.geojson`: AV polygon used for the mobility accessibility analysis
- `data/input_od/Shape_zone.SHP`: zone polygons
- `data/input_od/Shape_zone_centroid.SHP`: zone centroids
- `data/input_od/PROGETTO-OD.xlsx`: OD flows between zones
- `data/input_service/nord-est-260826.osm.pbf`: regional OSM extract for the Bologna area (Geofabrik)
- `data/input_service/gommagtfsbo_20250513.zip`: GTFS feed for the local public transport network

## Configuration and project paths

The project centralizes paths and defaults in:

- `runners/paths.py`
- `runners/config.py`
- `src/otp_mobility/utils/config.py`
- `src/otp_mobility/utils/constants.py`

This keeps the data workflow reproducible and makes it easier to swap input/output folders or simulation parameters.

## Main workflow

### 1. Prepare OD data

The script `runners/get_OD_points.py` builds the OD datasets used by OTP from the zone polygons, centroids and the OD matrix.

It creates three dataset variants:

- `data/output/od-coords-extended.parquet`: all OD pairs from outside to inside AV
- `data/output/od-coords-simplified.parquet`: outside origins aggregated toward a single flow-weighted AV destination
- `data/output/od-coords-av.parquet`: OD pairs entirely within AV

The logic is implemented in the preparation utilities under `src/otp_mobility/preparation/` and is built around zone classification inside/outside the AV, centroid operations and flow aggregation.

Run it with:

```bash
uv run python runners/get_OD_points.py
```

### 2. Prepare OSM service data

The OSM preparation pipeline is implemented in `runners/get_OSM_data_with_pyosmium.py` and executes a sequence of processing steps:

1. Extract the Bologna bounding box from the OD coordinates
2. Extract the relevant OSM objects from the regional dataset
3. Filter the tags needed for mobility analysis
4. Enhance parking data by tagging park-and-ride facilities and removing duplicates
5. Resize the AV polygon to model restricted access conditions
6. Extract OSM features inside AV and outside AV
7. Add car restriction rules to the inside-AV network layer

The generated outputs are stored in `data/output/` and `data/output/tmp/`.

Key generated files include:

- `bologna-area-filtered-parking.osm.pbf`
- `bologna-area-filtered-parking-inside-AV.osm.pbf`
- `bologna-area-filtered-parking-inside-AV-footway.osm.pbf`
- `bologna-area-filtered-parking-outside-AV.osm.pbf`

Run the pipeline with:

```bash
uv run python runners/get_OSM_data_with_pyosmium.py
```

An alternative Osmium CLI workflow is also available in `runners/get_OSM_data_with_osmiumtool.sh`.

### 3. Generate OTP configuration

The OTP configuration is produced by `src/otp_mobility/otp/generate_config.py`.

It creates:

- a static configuration with OSM and GTFS sources
- a routing configuration for OTP defaults such as search window and walking reluctance

The generated configuration files are written under `data/output/` as `build-config.json` and `routing-config.json`.

### 4. Run OTP simulations

The routing logic is implemented in `src/otp_mobility/otp/processor.py` and performs batch GraphQL queries against the OTP endpoint.

Supported transport modes include combinations such as:

- `CAR_PARK`
- `TRANSIT`
- `WALK`
- mixed multimodal combinations

The project also includes logic to retry queries with small coordinate jitter when a route is not found, helping recover from edge cases in the network representation.

#### Local execution

1. Install Java
2. Download the OTP jar, for example `otp-shaded-2.7.0.jar`, and place it in a convenient local path. Set the path in `runners/path.py` under the variable `otp_jar_file`.
3. Then run the local simulation script:

```bash
uv run python runners/run_otp_simulation_locally.py
```

Simulation parameters and mode sets are defined in `runners/config.py`.

#### Remote execution

Remote execution is supported via the notebook `runners/run_otp_simulation_remotely.ipynb`.

This workflow targets a DigitalHub/OTP platform environment and is useful when the routing engine is executed remotely instead of locally. Before running it, verify the OTP endpoint, GTFS and OSM locations, and the selected OD dataset.

### 5. Postprocessing

The notebooks in `notebooks/postprocessing/` are used to inspect and validate the simulation output:

- `check_extended_results.ipynb`
- `check_simplified_results.ipynb`

These notebooks are intended to compare travel-time characteristics across the extended and simplified OD scenarios before further analysis.

## Typical execution sequence

```bash
uv sync
uv run python runners/get_OD_points.py
uv run python runners/get_OSM_data_with_pyosmium.py
uv run python runners/run_otp_simulation_locally.py
```

## Notes

- The project mixes local preprocessing and remote OTP execution.
- `WALK` is automatically added to route requests when needed by the simulation layer.
- Results are typically stored in `data/output/` as Parquet tables and OSM extracts.
- The project is built around Bologna-specific constraints such as AV access rules, park-and-ride integration and multi-modal travel-time analysis.

