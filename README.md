# OpenTripPlanner — Bologna Case Study

This repository provides a structured setup for extracting travel times with **OpenTripPlanner (OTP)**, with the final goal of comparing travel times between zones using different transport modes.

## Workflow Overview
The project is organized in three main phases:

- *preparation*: Create input files for OTP simulations. Most code is contained in the folder `preparation/`.
- *OTP Simulations*: Compute travel times between zones. Mainly implemented through the code in `otp-processor.py`.
- *Postprocessing*: Analyze simulation outputs. Most code is contained in the folder `postprocessing/`.

## Python Environment

The Python environment is managed with [uv](https://docs.astral.sh/uv/). Project metadata and dependencies are declared in `pyproject.toml`, while the exact resolved versions are tracked in `uv.lock`.

From the project root, install uv and create the virtual environment and its dependencies with:

```bash
uv venv
uv sync
```

Run Python scripts through the managed environment with `uv run`, for example:

```bash
uv run python runners/get_OD_points.py
```

## 1. Preparation

**Goal**: Load and/or generate the input files required for OTP simulations, specifically:
- *OD coords points*: Parquet files describing all the combinations of origin and destination zones.
- *OSM data*: OpenStreetMap network files, relaborated from source to focus on the Bologna area and the task of interest.
- *Service data*: .zip files, downloaded from source, listing the routes and schedules of the public transports in the area.

### OD coords point
The implementation of this pipeline is in the script `runners/geo_OD_points.py`. It extracts the centroids of the zones in the Province of Bologna, recording latitude, longitude, and zone ID, and generates all origin–destination (OD) combinations, which are then written to the output files.

The analysis requires the following **input files**. All input files must be placed in the `data` folder.
- the geographical boundaries of the Area Verde in the file `input_geo/area_verde_manual_v1.geojson`.
- the centroids and shapes of the PUMS areas in the files `input_od/Shape_zone_centroid.SHP` and `input_od/Shape_zone.SHP` respectively.
- the flows from all combinations of origin and destination zones, saved in the file `input_od/PROGETTO-OD.xlsx`.

The processing pipeline **outputs three files** used in the next OTP simulation and saved in the `data/output_preparation` folder:
- `od-coords-extended`: contains the coordinates of OD pairs where the origin lies outside the Area Verde and the destination lies inside it.
- `od-coords-simplified`: aggregates all zones within the Area Verde into a single polygon, providing coordinates for origins outside the area and a single centroid representing the destination.
- `od-coords-av`, contains the coordinates of OD pairs with both origin and destination inside the Area Verde

The implementation supports both **local and remote writing** of the data:
- For saving locally, files are read from and written to the directory `data/output_preparation`.
- For saving on the datalake, use the project `test-otp-v2` and the functionalities of `digitalhub` to store data on the prokect data lake.

### OSM data
OpenStreetMap (OSM) data are processed using Osmium to rework an input OSM file for the region.

The **input file** is `nord-est-latest.osm.pbf`, which can be downloaded from [Geofabrik](https://download.geofabrik.de/europe/italy/nord-est.html).
*Note: the version used in this analysis was downloaded on 2025-05-27.*

The processing pipeline **outputs three files** used in the next OTP simulation, saved in the folder `data/output_preparation`:
- `bologna-area-filtered-parking.osm.pbf`: all OSM elements of interest in the Bologna province.
- `bologna-area-filtered-parking-inside-AV-footway.osm.pbf`: all OSM elements of interest in the Area Verde, with modified tags to limit vehicular access.
- `bologna-area-filtered-parking-outside-AV.osm.pbf`all OSM elements of interest outside the Area Verde.

The **processing workflow** consists of several steps of area extraction, tag filtering, and tag modification. All of these are implemented in the script `runners/get_OSM_data_with_pyosmium.py`.
If **osmium-tool** is installed, the same pipeline can be executed more efficiently using the commands provided in `runners/get_OSM_data_with_osmiumtool.sh`.

**Notes:**
* `pyosmium` and `geopandas` are required to run the scripts. They are installed automatically by `uv sync` from the dependencies declared in `pyproject.toml`.
* Place the main input file in the folder `data/input_service`. All output files will be saved in this directory.

### Service data
These are the GTFS service data, which describe public transport routes and schedules.

For this analysis, only the TPER bus data were used. They are provided in the zip folder `gommagtfsbo_20250513.zip`, which can be downloaded from [Solweb TPER](https://solweb.tper.it/web/tools/open-data/open-data.aspx). *Note: the version used in this analysis was downloaded on 2025-05-27.*

## 2. OTP Simulations

**Goal**: Query OTP to compute travel times between zones using different transport modes.

You can run simulations either *locally*, with a direct execution with OTP server, or *on cluster*, with a distributed execution on HPC cluster. Different steps are required to execute OTP in the two ways.

### Option A: Local execution

The first step is to insall OTP:
1. Ensure that Java is installed (it is required to run OTP)
2. Download **OTP** (`otp-shaded-2.7.0.jar`) from [Maven Central](https://repo1.maven.org/maven2/org/opentripplanner/otp-shaded/2.7.0/)
3. Place the file in the **main folder of this repository**

In the same folder, locate the `.zip` file(s) of the GTSF data describing the service, and the `.pbf` file(s) of the road network and facilities. 

From the project folder, launch OTP with:
```bash
java -Xmx2G -jar otp-shaded-2.7.0.jar --build --serve .
```
This instruction will build the transportation graph from the input data and activate the simulator.

To excute the queries, **run the main script** `otp-processor.py`:
```bash
python otp_processor.py XXX
```
where `XXX` represent a sequence of one or more modes of transport values from:
- `"CAR"`: travel by car  
- `"TRANSIT"`: travel by public transport  
- `"WALK"`: travel by walking (always added as an available mode)
The script is able to read both local and remote data. Set the location of the data in the `src/params.py` list.

**Note**: OTP must be running while queries are executed.

### Option B: Cluster Execution

First, we need to create and actiate the OTP container on the server. This is done in the first part of the notebook `otp-to-platform.ipynb`.
Then, the same notebook is used to launch the simulation job.

**Remember:** The notebook have most parameters fixed, other changing over simulation. Always check, and possibly change:
- The link to access the artifacts of the `.zip` and `.pbf` data on s3
- The url of the container where OTP is running
- The s3 location of the input OD point data
- The input parameters of the simulation (e.g., modes of transport, OD points)

**Note**: On cluster, only remote data access is available

## 3. Postprocessing

**Goal**: Analyze simulation outputs to extract insights and compare travel times.

If output data are saved locally, they can be found in: `data/output/`. 

