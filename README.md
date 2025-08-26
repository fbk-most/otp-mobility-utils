# OpenTripPlanner — Bologna Case Study

This repository provides a structured setup for extracting travel times with **OpenTripPlanner (OTP)**, with the final goal of comparing travel times between zones using different transport modes.

## 1. Installation

1. Download **OTP** (`otp-shaded-2.7.0.jar`) from [Maven Central](https://repo1.maven.org/maven2/org/opentripplanner/otp-shaded/2.7.0/).
2. Place the file in the **main folder of this repository**.

## 2. Running OpenTripPlanner

From the project folder, launch OTP with:

```bash
java -Xmx2G -jar otp-shaded-2.7.0.jar --build --serve
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

## 4. Input Data

To work properly, the following input data are required. See `bologna_preprocessing/README.md` for the details on the methodology of data extraction and manipulation.

### Infrastructure and service data
Two are the service data types required for the simulation. 

- A `.pbf` file containing the OpenStreetMap road network.
- `.zip` folder(s) containing the **GTFS schedule**(s) for public transportation.

After their creation, they must be copied and located in the main folder of the project. 

### Origin–Destination points
Located in `data/input_od/`, they represent the start and end points of the trips for which travel times are assessed.


## 5. Output Data

The computed travel times are saved in: `data/output/`
