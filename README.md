# OpenTripPlanner — Bologna Case Study

This repository provides a structured setup for extracting travel times with **OpenTripPlanner (OTP)**, with the final goal of comparing travel times between zones using different transport modes.

## Workflow Overview
The project is organized in three main phases:

- *Preprocessing*: Create input files for OTP simulations. Most code is contained in the folder `preprocessing/`.
- *OTP Simulations*: Compute travel times between zones. Mainly implemented through the code in `otp-processor.py`.
- *Postprocessing*: Analyze simulation outputs. Most code is contained in the folder `postprocessing/`.

## 1. Preprocessing

**Goal**: Generate the input files required for OTP simulations, specifically:
- *OD coords points*: Parquet files describing all the combinations of origin and destination zones in the script `preprocessng/geo_OD_points.py`.
- *OSM data*: OpenStreetMap network files, relaborated from source to focus on the Bologna area and the task of interest in the script `preprocessing/get_OSM_data.py`.

You can run preprocessing either *locally* on your machine *on platform* (e.g., Jupiter Lab)
- For working locally, first create a virtual environment where to download all the requirements: `dhcli` (to be configured and logged in), `geopandas`, `shapely`, `osmium`.
- For working on platform, **TODO**: Configuration steps to be defined

While all raw input data are to be loaded locally (**TODO**: allow them to be found in the datalake), the preprocessing output data can be saved either *locally* or *on the data lake*. 
- For saving locally, use the folder `data` where to create three subfolders `input_service` for OSM data, `input_od` for OD points, and `output`.
- For saving on the datalake, use the project `test-otp-v2` and the functionalities of `digitalhub` to save data.
- Locate the raw input data in `input_service` and `input_od` according to the preprocessing phase in which they are used.

## 2. OTP Simulations

**Goal**: Query OTP to compute travel times between zones using different transport modes.

You can run simulations either *locally / on platform*, with a direct execution with OTP server, or *on cluster*, with a distributed execution on HPC cluster. Different steps are required to execute OTP in the two ways.

### Input Data Details

Regarding infrastructure and Service Data, two types of  data are required:

- **`.pbf` file(s)**: OpenStreetMap road network
  - `bologna-area-filtered-parking-sorted.osm.pbf` for current situation trips (unimodal and multimodal)
  - `bologna-area-filtered-parking-inside-AV-footway.osm.pbf` and `bologna-area-filtered-parking-outside-AV.osm.pbf` to force intermodality entering Area Verde (private vehicles kept outside)

- **`.zip` folder(s)**: GTFS schedules for public transportation

The simulation is executed between each **OD pairs** contained in the file of OD coord points. It represents start and end points for trips.
- `od-coords-extended`: origins are the centroids outside Area Verde, and destinations are the centroids inside Area Verde
- `od-coords-simplified`: origins are the centroids outside Area Verde, and destination is the centroid of Area Verde
- `od-coords-av`: origins and destinations are the centroids inside Area Verde

### Option A: Local / Platform Execution

The first step is to insall OTP:
1. Ensure that Java is installed (it is required to run OTP)
2. Download **OTP** (`otp-shaded-2.7.0.jar`) from [Maven Central](https://repo1.maven.org/maven2/org/opentripplanner/otp-shaded/2.7.0/)
3. Place the file in the **main folder of this repository**

In the same folder, locate the `.zip` file(s) of the gtfs data describing the service, and the `.pbf` file(s) of the road network and facilities. 

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

First, we need to create and actiate the OTP container on the server. This is done in the first part of the notebook **`otp-to-platform.ipynb`**.
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

