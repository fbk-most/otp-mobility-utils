"""
Tentative implementation of the tag-filter function from osmium-tool. 

Taken from the osmium-tool documentation: 'All objects matching the expressions will be read from OSM-FILE and written to the output. All objects referenced from those objects will also be added to the output [...]. This applies to nodes referenced in ways and members referenced in relations.'
https://docs.osmcode.org/osmium/latest/osmium-tags-filter.html

We add to a new file all nodes, ways, and relations that have at least one of the key-tag combinations explicited in the filter file, and we add all of their references through a back-reference writer. The implementation is based on this suggestion from the package author: https://github.com/osmcode/pyosmium/discussions/274

Note: assumptions: nodes are filtered based on the "n*/" lines of the filter file; ways based on the "w*/" lines; relations on the "r*/" lines, and if they are of type "multypolygon" they consider also the "a*/" lines (since they represent areas).

Note: this filter implementation is tested to work with our filters written in filter_expressiosn.sh. However, it is not straightforward that it will work with every filter (e.g., for sure it does not handle "!=" filters, or empty key tags).
"""

import osmium
from pathlib import Path
import sys
import os
sys.path.append(f"{os.path.expanduser('.')}/src")
from params import verbose
from datetime import datetime
from back_way_forward_reference_writer import BackWayForwardReferenceWriter
from parse_filter_expression import parse_filter_expression


def our_tags_filter_with_pyosmium(input_file, output_file, filter_file):
    # Read the filters
    full_filter_n, full_filter_w, full_filter_r, full_filter_a = parse_filter_expression(filter_file) 

    # Use a back-reference writer to guarantee completeness
    writer = osmium.BackReferenceWriter(output_file, ref_src=input_file, overwrite=True)

    # Read file, filter and write file
    print(f"-> Getting elems \n and it's {datetime.now().strftime('%H:%M:%S')}") if verbose else None
    fp = osmium.FileProcessor(input_file)
    osmium_filters = [
        osmium.filter.KeyFilter(*full_filter_n.keys()).enable_for(osmium.osm.NODE),
        osmium.filter.KeyFilter(*full_filter_w.keys()).enable_for(osmium.osm.WAY),
        osmium.filter.KeyFilter(*full_filter_r.keys(), *full_filter_a.keys()).enable_for(osmium.osm.RELATION)
    ]
    for f in osmium_filters:
        fp = fp.with_filter(f)
    for obj in fp:
        if obj.is_node():
            if obj.id == 2416635617:
                print(obj)
        if obj.is_node() and _check_condition(obj.tags, full_filter_n):
            writer.add_node(obj)
        elif obj.is_way() and _check_condition(obj.tags, full_filter_w):
            writer.add_way(obj)
        elif obj.is_relation() and _check_condition_relations(obj.tags, full_filter_r, full_filter_a):
            writer.add_relation(obj)
    print(f"-> It's {datetime.now().strftime('%H:%M:%S')}\n and we are almost closing!") if verbose else None
    writer.close()
    print(f"-> It's {datetime.now().strftime('%H:%M:%S')}\n and we've finished!") if verbose else None

    # Print stats
    if verbose:
        _show_stats([0,0,0], input_file, output_file)

def _check_condition(tags, filter):
    for t in tags:
        if t.k in filter.keys():
            if (not filter.get(t.k)) or (filter.get(t.k) and t.v in filter.get(t.k)):
                    return True
    return False

def _check_condition_relations(tags, filter1, filter2):
    additional_check = False
    for t in tags:
        if t.k == "type" and t.v == "multipolygon":
            additional_check = True
        if t.k in filter1.keys():
            if (not filter1.get(t.k)) or (filter1.get(t.k) and t.v in filter1.get(t.k)):
                    return True
    if additional_check:
        for t in tags:
            if t.k in filter2.keys():
                if (not filter2.get(t.k)) or (filter2.get(t.k) and t.v in filter2.get(t.k)):
                        return True
    return False

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
    
def _show_stats(n_objects, input_file: str, output_file: str):
    # N. elements
    i_in, i_iw, i_ir = _count_elements(input_file)
    i_on, i_ow, i_or = _count_elements(output_file)
    print(f"-> How many in the original file: {i_in} nodes, {i_iw} ways, {i_ir} relations")
    print(f"   How many explicitly added: {n_objects[0]} nodes, {n_objects[1]} ways, {n_objects[2]} relations") 
    print(f"   How many in the output file: {i_on} nodes, {i_ow} ways, {i_or} relations")  

    # Sizes
    original_size = Path(input_file).stat().st_size / (1024 * 1024)
    filtered_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"-> Original size: {original_size:.2f} MB")
    print(f"   New size: {filtered_size:.2f} MB")


if __name__ == "__main__":
    # Configuration
    input_file = Path("data/input_service/bologna-area.osm.pbf")
    output_file = Path("data/input_service/bologna-area-filtered.osm.pbf")
    filter_file = Path("data/input_service/filter_expression.sh")

    our_tags_filter_with_pyosmium(str(input_file), str(output_file), str(filter_file))