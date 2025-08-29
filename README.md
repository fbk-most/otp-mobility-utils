# OpenTripPlanner — Bologna Case Study

This repository provides a structured setup for extracting travel times with **OpenTripPlanner (OTP)**, with the final goal of comparing travel times between zones using different transport modes.

## 1. Installation

1. Download **OTP** (`otp-shaded-2.7.0.jar`) from [Maven Central](https://repo1.maven.org/maven2/org/opentripplanner/otp-shaded/2.7.0/).
2. Place the file in the **main folder of this repository**.

## 2. Running OpenTripPlanner

From the project folder, launch OTP with:

```bash
java -Xmx2G -jar otp-shaded-2.7.0.jar --build --serve .
```

- OTP must be running while queries are executed.  
- Some default OTP values were modified for this setup — see `router-config.json` for details.


## 3. Core Script

- The main processing script is **`otp-processor.py`**.  
- It queries OTP to compute possible travel solutions and returns travel times between zones.

Usage:
```bash
python otp_processor.py XXX
```

Where:
- `XXX = "CAR"` → travel by car  
- `XXX = "TRANSIT"` → travel by public transport  
- `XXX = "WALK"` → travel by walking  

## 4. Input Data

To work properly, the following input data are required. See `bologna_preprocessing/README.md` for the details on the methodology of data extraction and manipulation.

### Infrastructure and service data
Two are the service data types required for the simulation. 

- `.pbf` file(s) containing the OpenStreetMap road network.
  - use `bologna-area-filtered-sorted.osm.pbf` for trips, both unimodal and multimodal, considering the current situation. 
  - use `bologna-area-filtered-inside-AV-footway.osm.pbf` and `bologna-area-filtered-outside-AV-parking.osm.pbf` to force intermodality to enter Area Verde (since provate vehicels are kept outside)
- `.zip` folder(s) containing the **GTFS schedule**(s) for public transportation.

After their creation, they must be copied and located in the main folder of the project. 

### Origin–Destination points
Located in `data/input_od/`, they represent the start and end points of the trips for which travel times are assessed.


## 5. Output Data

The computed travel times are saved in: `data/output/`


## 6. Config files

- `build-config.json`:
  Options and parameters that are taken into account during the graph building process will be "baked into" the graph, and cannot be changed later in a running server.
  - `"staticParkAndRide": true` Whether we should create car P+R stations from OSM data.
  - `"matchBusRoutesToStreets": true` Based on GTFS shape data, guess which OSM streets each bus runs on to improve stop linking.
  - `"platformEntriesLinking": true` Link unconnected entries to public transport platforms.
  - `"fare": XXX` Fare configuration. _Se fossero disponibili nel GTFS..._
  - `gtfsDefaults` > `"maxInterlineDistance": 200` Maximal distance between stops in meters that will connect consecutive trips that are made with same vehicle.. _Da aumentare a 500_

- `router-config.json`:
  Other details of OTP operation can be modified without rebuilding the graph, i.e., run-time configuration options.
    - itineraryFilters > parkAndRideDurationRatio 0 
    -  wheelchairAccessibility  stop onlyConsiderAccessible _set to false_

- `otp-config.json`:
  Simple switches that enable or disable system-wide features. ????