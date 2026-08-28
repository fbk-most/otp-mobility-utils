#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
DATA_DIR="${PROJECT_ROOT}/data"
INPUT_GEO_DIR="${DATA_DIR}/input_geo"
INPUT_SERVICE_DIR="${DATA_DIR}/input_service"

export PYTHONPATH="${PROJECT_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

INPUT_OSM="${INPUT_SERVICE_DIR}/nord-est-260826.osm.pbf"
AREA_VERDE_INPUT="${INPUT_GEO_DIR}/area_verde_manual_v1.geojson"
AREA_VERDE_UTM="${INPUT_SERVICE_DIR}/area_verde_manual_v1_utm.geojson"
SMALL_AREA_VERDE_UTM="${INPUT_SERVICE_DIR}/small_area_verde_manual_v1_utm.geojson"
SMALL_AREA_VERDE="${INPUT_SERVICE_DIR}/small_area_verde_manual_v1.geojson"

if [[ ! -f "${INPUT_OSM}" ]]; then
    echo "Missing OSM file: ${INPUT_OSM}"
    exit 1
fi

if [[ ! -f "${AREA_VERDE_INPUT}" ]]; then
    echo "Missing Area Verde file: ${AREA_VERDE_INPUT}"
    exit 1
fi

echo "SERVICE DATA PIPELINE START"

echo "► Step 2: Extract Bologna area from regional OSM file using bounding box"

osmium extract \
    --bbox 10.734269464357556,43.96629819030445,12.139133497965453,44.91004596649926 \
    "${INPUT_OSM}" \
    --overwrite -o "${INPUT_SERVICE_DIR}/bologna-area.osm.pbf"


echo "► Step 3: Filter relevant entities (roads and features) for mobility analysis"

osmium tags-filter \
    "${INPUT_SERVICE_DIR}/bologna-area.osm.pbf" \
    -e "${INPUT_SERVICE_DIR}/filter_expression.sh" \
    -o "${INPUT_SERVICE_DIR}/bologna-area-filtered.osm.pbf" --overwrite -f pbf,add_metadata=false


echo "► Step 4: Correct parking data to enable park-and-ride intermodality"

python3 "${PROJECT_ROOT}/src/otp_mobility/preparation/add_parkrides.py" \
    "${INPUT_SERVICE_DIR}/bologna-area-filtered.osm.pbf" \
    "${INPUT_SERVICE_DIR}/bologna-area-filtered-parking.osm.pbf"


echo "► Step 5: Apply negative 250m buffer to 'Area Verde' zone"

ogr2ogr \
    -f GeoJSON "${AREA_VERDE_UTM}" \
    "${AREA_VERDE_INPUT}" \
    -t_srs EPSG:6875

ogr2ogr \
    -f GeoJSON "${SMALL_AREA_VERDE_UTM}" \
    "${AREA_VERDE_UTM}" \
    -dialect SQLite -sql "SELECT ST_Buffer(geometry, -250) AS geometry FROM area_verde_manual_v1"

ogr2ogr \
    -f GeoJSON "${SMALL_AREA_VERDE}" \
    "${SMALL_AREA_VERDE_UTM}" \
    -t_srs EPSG:4326


echo "ADDITIONAL STEPS FOR INTERMODALITY ANALYSIS"

echo "► Step 6: Extract OSM elements inside the 'Area Verde' polygon"

osmium extract \
    --polygon "${SMALL_AREA_VERDE}" \
    "${INPUT_SERVICE_DIR}/bologna-area-filtered-parking.osm.pbf" \
    -o "${INPUT_SERVICE_DIR}/bologna-area-filtered-parking-inside-AV.osm.pbf" --overwrite


echo "► Step 7: Extract OSM elements outside the 'Area Verde' polygon"

python3 "${PROJECT_ROOT}/src/otp_mobility/preparation/extract_elements_outside.py" \
    "${INPUT_SERVICE_DIR}/bologna-area-filtered-parking.osm.pbf" \
    "${INPUT_SERVICE_DIR}/bologna-area-filtered-parking-inside-AV.osm.pbf" \
    "${INPUT_SERVICE_DIR}/bologna-area-filtered-parking-outside-AV.osm.pbf"


echo "► Step 8: Add car restrictions to entering in the Area Verde"

python3 "${PROJECT_ROOT}/src/otp_mobility/preparation/add_car_restrictions.py" \
    "${INPUT_SERVICE_DIR}/bologna-area-filtered-parking-inside-AV.osm.pbf" \
    "${INPUT_SERVICE_DIR}/bologna-area-filtered-parking-inside-AV-footway.osm.pbf"


echo "PIPELINE END"
