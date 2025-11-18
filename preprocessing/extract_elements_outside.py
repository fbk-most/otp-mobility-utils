import osmium
import shapely.geometry as geom
from datetime import datetime
import json
import sys
import os
from pathlib import Path
sys.path.append(f"{os.path.expanduser('.')}/src")
from params import verbose


def extract_elements_outside(input_file_container: str, input_file_contained: str, output_file:str):
    # Inizialize the ids file
    ids_nodes, ids_ways, ids_relations = set(), set(), set()
    
    # Read the contained file, and save the ids:
    fp = osmium.FileProcessor(input_file_contained)
    for obj in fp:
        if obj.is_node():
            ids_nodes.add(obj.id)
        elif obj.is_way():
            ids_ways.add(obj.id)
        elif obj.is_relation():
            ids_relations.add(obj.id)

    # Writer OSM
    writer = osmium.SimpleWriter(output_file, overwrite=True)

    # Load the container file
    fp = osmium.FileProcessor(input_file_container)
    for obj in fp:
        if obj.is_node() and obj.id not in ids_nodes:
            writer.add_node(obj)
        elif obj.is_way() and obj.id not in ids_ways:
            writer.add_way(obj)
        elif obj.is_relation() and obj.id not in ids_relations:
            writer.add_relation(obj)
    print(f"-> It's {datetime.now().strftime('%H:%M:%S')}\n and we are almost closing!") if verbose else None
    writer.close()
    print(f"-> It's {datetime.now().strftime('%H:%M:%S')}\n and we've finished!") if verbose else None

    if verbose:
        _show_file_sizes(input_file_container, input_file_contained, output_file)


def _count_elements(input_file: str):
    i_in, i_iw, i_ir = 0, 0, 0
    for obj in osmium.FileProcessor(input_file):
        if obj.is_node():
            i_in = i_in+1  
        elif obj.is_way():
            i_iw = i_iw + 1
        elif obj.is_relation():
            i_ir = i_ir +1 
    return i_in, i_iw, i_ir
    
def _show_file_sizes(input_file_container: str, input_file_contained: str, output_file:str):
    # N. elements
    i_in, i_iw, i_ir = _count_elements(input_file_container)
    i_i2n, i_i2w, i_i2r = _count_elements(input_file_contained)
    i_on, i_ow, i_or = _count_elements(output_file)
    print(f"-> How many in the original container file: {i_in} nodes, {i_iw} ways, {i_ir} relations")
    print(f"   How many in the original contained file: {i_i2n} nodes, {i_i2w} ways, {i_i2r} relations")
    print(f"   How many in the output file: {i_on} nodes, {i_ow} ways, {i_or} relations")  

    # Sizes
    original_container_size = Path(input_file_container).stat().st_size / (1024 * 1024)
    original_contained_size = Path(input_file_contained).stat().st_size / (1024 * 1024)
    filtered_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"-> Original container size: {original_container_size:.2f} MB")
    print(f"   Original contained size: {original_contained_size:.2f} MB")
    print(f"   New size: {filtered_size:.2f} MB")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Error: wrong number of inputs. Given {len(sys.argv)-1}, while needed 3.")
        print("Correct usage: python extract_elements_outside.py input_container input_contained output")
        sys.exit(1)
    
    # Configuration
    input_file_container = sys.argv[1]
    input_file_contained = sys.argv[2]
    output_file = sys.argv[3]
    print(f"Executing add_parkrides.py with: \n- input_container = {input_file_container}\n- input_contained = {input_file_contained}\n- output = {output_file}\n")

    extract_elements_outside(input_file_container, input_file_contained, output_file)
    print("\n")