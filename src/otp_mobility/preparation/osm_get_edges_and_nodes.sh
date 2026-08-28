#!/bin/bash

echo "Conversione OSM a rete stradale (EPSG:6875)..."

cat > process_network.py << 'EOF'
import json
import subprocess
import math
import geopandas as gpd
from collections import defaultdict, OrderedDict
from statistics import median

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def parse_maxspeed(maxspeed_str):
    if not maxspeed_str:
        return None
    speed_str = maxspeed_str.replace('km/h', '').replace('mph', '').replace(' ', '')
    try:
        return float(speed_str) / 3.6
    except:
        return None

def parse_lanes(lanes_str):
    if not lanes_str:
        return None
    try:
        return int(lanes_str)
    except:
        return None

def is_oneway(oneway_tag):
    if not oneway_tag:
        return False
    return str(oneway_tag).lower() in ['yes', '1', 'true']

def calculate_medians(geojson_data):
    maxspeed_by_type = defaultdict(list)
    lanes_by_type = defaultdict(list)
    
    for feature in geojson_data['features']:
        properties = feature['properties']
        highway_type = properties.get('highway', 'unknown')
        
        maxspeed = parse_maxspeed(properties.get('maxspeed'))
        if maxspeed is not None:
            maxspeed_by_type[highway_type].append(maxspeed)
        
        lanes = parse_lanes(properties.get('lanes'))
        if lanes is not None:
            lanes_by_type[highway_type].append(lanes)
    
    median_maxspeed = {}
    median_lanes = {}
    
    fallback_maxspeed = {
        'motorway': 130/3.6, 'motorway_link': 80/3.6, 'trunk': 110/3.6, 'trunk_link': 70/3.6,
        'primary': 90/3.6, 'primary_link': 50/3.6, 'secondary': 70/3.6, 'secondary_link': 50/3.6,
        'tertiary': 50/3.6, 'tertiary_link': 40/3.6, 'unclassified': 50/3.6
    }
    
    fallback_lanes = {
        'motorway': 3, 'motorway_link': 1, 'trunk': 2, 'trunk_link': 1,
        'primary': 2, 'primary_link': 1, 'secondary': 2, 'secondary_link': 1,
        'tertiary': 1, 'tertiary_link': 1, 'unclassified': 1
    }
    
    for highway_type in maxspeed_by_type:
        if maxspeed_by_type[highway_type]:
            median_maxspeed[highway_type] = median(maxspeed_by_type[highway_type])
    
    for highway_type in lanes_by_type:
        if lanes_by_type[highway_type]:
            median_lanes[highway_type] = median(lanes_by_type[highway_type])
    
    for highway_type in fallback_maxspeed:
        if highway_type not in median_maxspeed:
            median_maxspeed[highway_type] = fallback_maxspeed[highway_type]
    
    for highway_type in fallback_lanes:
        if highway_type not in median_lanes:
            median_lanes[highway_type] = fallback_lanes[highway_type]
    
    return median_maxspeed, median_lanes

def process_network():
    subprocess.run(['osmium', 'export', 'bologna-highway-filtered.osm.pbf',
                   '--output-format=geojson', '--geometry-types=linestring',
                   '--output=temp_highways.geojson', '--overwrite'])
    
    with open('temp_highways.geojson', 'r') as f:
        geojson_data = json.load(f)
    
    median_maxspeed, median_lanes = calculate_medians(geojson_data)
    
    edges = []
    unique_nodes = OrderedDict()
    node_connections = defaultdict(list)
    
    for feature in geojson_data['features']:
        properties = feature['properties']
        geometry = feature['geometry']
        
        highway_type = properties.get('highway', 'unknown')
        way_id = properties.get('@id', 0)
        
        maxspeed = parse_maxspeed(properties.get('maxspeed'))
        if maxspeed is None:
            maxspeed = median_maxspeed.get(highway_type, 50/3.6)
        
        lanes = parse_lanes(properties.get('lanes'))
        if lanes is None:
            lanes = median_lanes.get(highway_type, 1)
        
        oneway = is_oneway(properties.get('oneway'))
        
        coordinates = geometry['coordinates']
        length = 0
        
        for i in range(len(coordinates) - 1):
            lon1, lat1 = coordinates[i]
            lon2, lat2 = coordinates[i + 1]
            length += haversine_distance(lat1, lon1, lat2, lon2)
        
        free_flow_time = length / maxspeed if maxspeed > 0 else float('inf')
        
        start_coord = coordinates[0]
        end_coord = coordinates[-1]
        
        u = f"{start_coord[1]:.6f}_{start_coord[0]:.6f}".replace('.', '').replace('-', 'n')
        v = f"{end_coord[1]:.6f}_{end_coord[0]:.6f}".replace('.', '').replace('-', 'n')
        
        node_pair = (u, v)
        key = len(node_connections[node_pair])
        node_connections[node_pair].append(way_id)
        
        link_id = f"{u}_{v}_{key}"
        
        if u not in unique_nodes:
            unique_nodes[u] = {
                'node_id': u,
                'coord1': start_coord[1],
                'coord2': start_coord[0],
                'geometry': {'type': 'Point', 'coordinates': start_coord}
            }
        
        if v not in unique_nodes:
            unique_nodes[v] = {
                'node_id': v,
                'coord1': end_coord[1],
                'coord2': end_coord[0],
                'geometry': {'type': 'Point', 'coordinates': end_coord}
            }
        
        edge = {
            'u': u, 'v': v, 'key': key, 'highway': highway_type,
            'length': round(length, 2), 'maxspeed': round(maxspeed, 2),
            'lanes': lanes, 'free_flow_time': round(free_flow_time, 2),
            'link_id': link_id, 'highway_ok': True, 'oneway': oneway,
            'geometry': geometry
        }
        
        edges.append(edge)
    
    edges_features = []
    for edge in edges:
        feature = {
            'type': 'Feature',
            'properties': {k: v for k, v in edge.items() if k != 'geometry'},
            'geometry': edge['geometry']
        }
        edges_features.append(feature)
    
    edges_geojson = {
        'type': 'FeatureCollection',
        'features': edges_features
    }
    
    with open('temp_edges_4326.geojson', 'w') as f:
        json.dump(edges_geojson, f)
    
    gdf_edges = gpd.read_file('temp_edges_4326.geojson')
    gdf_edges = gdf_edges.to_crs('EPSG:6875')
    gdf_edges.to_file('bologna-highway-edges.geojson', driver='GeoJSON')
    
    nodes_features = []
    for node_data in unique_nodes.values():
        feature = {
            'type': 'Feature',
            'properties': {
                'node_id': node_data['node_id'],
                'coord1': node_data['coord1'],
                'coord2': node_data['coord2']
            },
            'geometry': node_data['geometry']
        }
        nodes_features.append(feature)
    
    nodes_geojson = {
        'type': 'FeatureCollection',
        'features': nodes_features
    }
    
    with open('temp_nodes_4326.geojson', 'w') as f:
        json.dump(nodes_geojson, f)
    
    gdf_nodes = gpd.read_file('temp_nodes_4326.geojson')
    gdf_nodes = gdf_nodes.to_crs('EPSG:6875')
    
    for i, row in gdf_nodes.iterrows():
        x, y = row.geometry.x, row.geometry.y
        gdf_nodes.at[i, 'coord1'] = y
        gdf_nodes.at[i, 'coord2'] = x
    
    gdf_nodes.to_file('bologna-highway-nodes.geojson', driver='GeoJSON')
    
    print(f"Edges: {len(edges)} | Nodes: {len(unique_nodes)}")
    
    import os
    for temp_file in ['temp_highways.geojson', 'temp_edges_4326.geojson', 'temp_nodes_4326.geojson']:
        try:
            os.remove(temp_file)
        except:
            pass

if __name__ == "__main__":
    process_network()
EOF

python3 process_network.py
rm -f process_network.py

echo "Completato: bologna-highway-edges.geojson e bologna-highway-nodes.geojson (EPSG:6875)"