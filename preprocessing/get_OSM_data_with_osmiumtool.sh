#!/bin/bash

echo "SERVICE DATA PIPELINE START"

echo "► Step 2: Extract Bologna area from regional OSM file using bounding box"

osmium extract \
    --bbox 10.734269464357556,43.96629819030445,12.139133497965453,44.91004596649926 \
    data/input_service/nord-est-latest.osm.pbf \
    --overwrite -o data/input_service/bologna-area.osm.pbf
    

echo "► Step 3: Filter relevant entities (roads and features) for mobility analysis"

osmium tags-filter \
    data/input_service/bologna-area.osm.pbf \
    -e data/input_service/filter_expression.sh \
    -o data/input_service/bologna-area-filtered.osm.pbf --overwrite -f pbf,add_metadata=false


echo "► Step 4: Correct parking data to enable park-and-ride intermodality"

python preprocessing/add_parkrides.py \
    data/input_service/bologna-area-filtered.osm.pbf \
    data/input_service/bologna-area-filtered-parking.osm.pbf


echo "► Step 5: Apply negative 250m buffer to 'Area Verde' zone"

ogr2ogr \
    -f GeoJSON data/input_service/area_verde_manual_v1_utm.geojson \
    data/input_service/area_verde_manual_v1.geojson \
    -t_srs EPSG:6875

ogr2ogr \
    -f GeoJSON data/input_service/small_area_verde_manual_v1_utm.geojson \
    data/input_service/area_verde_manual_v1_utm.geojson \
    -dialect SQLite -sql "SELECT ST_Buffer(geometry, -250) AS geometry FROM area_verde_manual_v1"

ogr2ogr \
    -f GeoJSON data/input_service/small_area_verde_manual_v1.geojson \
    data/input_service/small_area_verde_manual_v1_utm.geojson \
    -t_srs EPSG:4326


echo "ADDITIONAL STEPS FOR INTERMODALITY ANALYSIS"

echo "► Step 6: Extract OSM elements inside the 'Area Verde' polygon"

osmium extract \
    --polygon data/input_service/small_area_verde_manual_v1.geojson \
    data/input_service/bologna-area-filtered-parking.osm.pbf \
    -o data/input_service/bologna-area-filtered-parking-inside-AV.osm.pbf --overwrite


echo "► Step 7 : Extract OSM elements outside the 'Area Verde' polygon"

python preprocessing/extract_elements_outside.py \
    data/input_service/bologna-area-filtered-parking.osm.pbf \
    data/input_service/bologna-area-filtered-parking-inside-AV.osm.pbf \
    data/input_service/bologna-area-filtered-parking-outside-AV.osm.pbf


echo "► Step 8: Add car restrictions to entering in the Area Verde"

python preprocessing/add_car_restrictions.py \
    data/input_service/bologna-area-filtered-parking-inside-AV.osm.pbf \
    data/input_service/bologna-area-filtered-parking-inside-AV-footway.osm.pbf 


echo "PIPELINE END"
