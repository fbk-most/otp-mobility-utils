# Service Input Data & Processing Pipeline

These are the instructions to get and process the main input data from sources. All these files are contained in the folder `data/input_service` of this project.  

## 1. GTFS of the transport service
- **File:** all files inside the folder `gommagtfsbo_20250513`  
- **Source:** [Solweb TPER](https://solweb.tper.it/web/tools/open-data/open-data.aspx)  
- **Download date:** 2025-05-27  


## 2. Road network PBF generation

This files are created starting from the [OTP Basic Tutorial](https://docs.opentripplanner.org/en/latest/Basic-Tutorial/), using [Osmium tools](https://osmcode.org/osmium-tool/) to limit the extent with a buffer and filter highways.


### Step 1 — Download reference OSM file
- **File:** `nord-est-latest.osm.pbf`  
- **Source:** [Geofabrik](https://download.geofabrik.de/europe/italy/nord-est.html)  
- **Download date:** 2025-05-27  


### Step 2 — Extract Bologna area
Run the code in extracted_bbox_from_OD.py to get the coordinates of the bouding box:
```bash
python preprocessing/extracted_bbox_from_OD.py
>> 10.734269464357556,43.96629819030445,12.139133497965453,44.91004596649926
```

Reduce the data, limiting the area of interest with the bounding box:
```bash
osmium extract   --bbox 10.734269464357556,43.96629819030445,12.139133497965453,44.91004596649926   data/input_service/nord-est-latest.osm.pbf   --overwrite -o data/input_service/bologna-area.osm.pbf
```


### Step 3 — Filter main roads
Selecting main elements of interests.  Run:
```bash
./preprocessing/osm_mobility_filter.sh
```


### Step 4 — Correct the parkings
To allow for intermodality, the original dataset must be modified and corrected. Indeed, parkings are not tagged to be "park and ride", i.e., parkings where vehicles can stop to continue the trip by public transports. With the code in the Python script `osm_add_parkride.py`, all parkings are made "park and ride".
```bash
python preprocessing/osm_add_parkride.py
```

Then, to ensure the data to be in the format that OTP can read, delete the duplicated relations with this command from terminal:
```bash
osmium sort -o data/input_service/bologna-area-filtered-parking-sorted.osm.pbf data/input_service/bologna-area-filtered-parking.osm.pbf --overwrite
```

### Additional steps for intermodality analysis

#### Step 5 — Define the reduced "Area Verde" zone
Apply a negative 250m buffer to the original polygon. 

```bash
# 0. Locate the original area_verde_manual_v1.geojson file in the folder

# 1. Reproject GeoJSON from EPSG:4326 → EPSG:6875 (UTM 32N)
ogr2ogr -f GeoJSON data/input_service/area_verde_manual_v1_utm.geojson data/input_service/area_verde_manual_v1.geojson -t_srs EPSG:6875

# 2. Apply negative buffer of 250m
ogr2ogr -f GeoJSON data/input_service/small_area_verde_manual_v1_utm.geojson data/input_service/area_verde_manual_v1_utm.geojson -dialect SQLite -sql "SELECT ST_Buffer(geometry, -250) AS geometry FROM area_verde_manual_v1"

# 3. Reproject back to EPSG:4326
ogr2ogr -f GeoJSON data/input_service/small_area_verde_manual_v1.geojson data/input_service/small_area_verde_manual_v1_utm.geojson -t_srs EPSG:4326
```

#### Step 6 — Extract OSM elements inside the "Area Verde"
```bash
osmium extract   --polygon data/input_service/small_area_verde_manual_v1.geojson  data/input_service/bologna-area-filtered-parking-sorted.osm.pbf   -o data/input_service/bologna-area-filtered-parking-inside-AV.osm.pbf --overwrite
```

#### Step 7 — Extract OSM elements outside the "Area Verde"
The elements outside the Area Verde are found with a difference between the whole dataset and the dataset within Area Verde. Generated using the Python script `osm_spatial_diff.py`:
```bash
python preprocessing/osm_spatial_diff.py
```

#### Step 8 — Prepare the elements inside the "Area Verde"
The Area Verde won't be accessible to private vehicles. Hence, modify the tags of all roads inside the Area Verde and make them unaccessible to private vehicles. This is done through the Python script `osm_convert_road_accessibility.py`:
```bash
python preprocessing/osm_convert_road_accessibility.py data/input_service/bologna-area-filtered-parking-inside-AV.osm.pbf  data/input_service/bologna-area-filtered-parking-inside-AV-footway.osm.pbf 
```

# OD Input Data & Processing Pipeline

These are the instructions to process the main input data about origin and destination trips. All these files are contained in the folder `data/input_od` of this project.  

## 1. Trips' starting and ending points

To construct the input file for OTP, ensure that the following files are located in the `data/input_od` folder:

- `Shape_zone.shp` and `Shape_zone_centroid.shp`, with the geometries of the OD zones;
- `area_verde_manual_v1.geojson`, with the geometry of the Area Verde zone;
- `PROGETTO-OD.xlsx`, with the flow counts between zones.

Then, built the file with the origin and destination points of trips through the code in `get_OD_points.py`. Run this from terminal:
```bash
python preprocessing/get_OD_points.py
```