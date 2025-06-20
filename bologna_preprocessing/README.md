# Input data
## Steps to obtain the pbf file of roads

1. `nord-est-latest.osm.pbf` scaricato da Geofabrik (data: 20250527) link https://download.geofabrik.de/europe/italy/nord-est.html

2. `bologna-area.osm.pbf` ridotto dal precedente usando la bbox della rete dei trasporti:
---> `osmium extract --bbox 10.734269464357556,43.96629819030445,12.139133497965453,44.91004596649926 nord-est-latest.osm.pbf --overwrite -o bologna-area.osm.pbf`

3. `bologna-highways.osm.pbf` ridotto dal precedente filtrando per strade principali
---> `osmium tags-filter bologna-area.osm.pbf highway=motorway highway=primary highway=secondary highway=tertiary highway=trunk highway=unclassified highway=motorway_link highway=primary_link highway=secondary_link highway=tertiary_link highway=trunk_link highway=unclassified_link --overwrite -o bologna-highways.osm.pbf`

## GTFS for transport service
- `gommagtfsbo_20250513`: gtfs di tper gomma scaricato da solweb-tper (data: 20250527) link https://solweb.tper.it/web/tools/open-data/open-data.aspx