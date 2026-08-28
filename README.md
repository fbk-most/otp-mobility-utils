# OpenTripPlanner - Bologna Case Study

This repository prepares OpenStreetMap and OD data and uses **OpenTripPlanner (OTP)** to compare travel times between zones in the Bologna area.

## Repository structure

- `runners/`: executable entry points for data preparation and OTP simulations.
- `src/otp_mobility/`: installable Python package containing the project logic.
	- `preparation/`: OSM, Area Verde and OD preparation utilities.
	- `otp/`: OTP configuration generation and GraphQL batch processing.
	- `utils/`: paths, constants and project configuration.
- `data/input_geo/`: Area Verde boundary.
- `data/input_od/`: zone geometries, centroids and OD flows.
- `data/input_service/`: OSM and GTFS input data.
- `data/output/`: generated OD files, OSM extracts, OTP configurations and results.
- `notebooks/postprocessing/`: notebooks for checking simulation results.

Paths are centralized in `runners/paths.py`; input and output files should therefore be placed in the directories above.

## Python environment

The project requires Python 3.12 or newer and uses [uv](https://docs.astral.sh/uv/) for dependency management. From the repository root:

```bash
uv venv
uv sync
```

Run scripts with the managed environment so that the `src/otp_mobility` package is available:

```bash
uv run python runners/get_OD_points.py
```

## Input data

Before running the pipelines, provide these files:

- `data/input_geo/area_verde_manual_v1.geojson`: Area Verde boundary.
- `data/input_od/Shape_zone_centroid.SHP` and `data/input_od/Shape_zone.SHP`: zone centroids and polygons.
- `data/input_od/PROGETTO-OD.xlsx`: origin-destination flows.
- `data/input_service/nord-est-260826.osm.pbf`: OSM extract, available from [Geofabrik](https://download.geofabrik.de/europe/italy/nord-est.html).
- `data/input_service/gommagtfsbo_20250513.zip`: TPER GTFS data, available from [Solweb TPER](https://solweb.tper.it/web/tools/open-data/open-data.aspx).

## 1. Prepare OD and OSM data

Generate the three OD datasets used by OTP:

```bash
uv run python runners/get_OD_points.py
```

The command writes the following files to `data/output/`:

- `od-coords-extended.parquet`: every OD pair from outside to inside the Area Verde.
- `od-coords-simplified.parquet`: outside origins and one flow-weighted Area Verde destination.
- `od-coords-av.parquet`: OD pairs whose origin and destination are inside the Area Verde.

Prepare the Bologna OSM extracts with pyosmium:

```bash
uv run python runners/get_OSM_data_with_pyosmium.py
```

The generated `.osm.pbf` files are written to `data/output/`, with intermediate files in `data/output/tmp/`. An alternative Osmium CLI workflow is available in `runners/get_OSM_data_with_osmiumtool.sh`.

## 2. Run OTP simulations

### Local execution

1. Install Java.
2. Download `otp-shaded-2.7.0.jar` from [Maven Central](https://repo1.maven.org/maven2/org/opentripplanner/otp-shaded/2.7.0/) and place it in the repository root.
3. Build and serve the OTP graph using the data in `data/output/`:

```bash
java -Xmx2G -jar otp-shaded-2.7.0.jar --build --serve data/output
```

With OTP running, execute the local simulation runner in a second terminal:

```bash
uv run python runners/run_otp_simulation_locally.py
```

The modes and simulation parameters are configured in `runners/config.py`. `WALK` is added automatically by the runner when needed. Results are saved as Parquet files in `data/output/`.

### Remote execution

Use `runners/run_otp_simulation_remotely.ipynb` to create or access the OTP container and launch a simulation on the platform. Before running it, check the S3 locations for GTFS, OSM and OD data, the OTP endpoint, and the selected simulation parameters. Remote execution uses the `test-otp-v2` DigitalHub project.

## 3. Postprocessing

Use the notebooks in `notebooks/postprocessing/` to inspect extended and simplified simulation results:

- `check_extended_results.ipynb`
- `check_simplified_results.ipynb`

Locally generated results are stored in `data/output/`.

