import osmium
from pathlib import Path
import sys
import os
sys.path.append(f"{os.path.expanduser('.')}/src")
from params import verbose
from datetime import datetime
from back_way_forward_reference_writer import BackWayForwardReferenceWriter
from parse_filter_expression import parse_filter_expression


def tag_filter_with_pyosmium2(input_file, output_file, filter_file):
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
        if obj.is_node() and check_condition(obj.tags, full_filter_n):
                writer.add_node(obj)
        elif obj.is_way() and check_condition(obj.tags, full_filter_w):
                writer.add_way(obj)
        elif obj.is_relation() and check_condition_relations(obj.tags, full_filter_r, full_filter_a):
            writer.add_relation(obj)
    print(f"-> It's {datetime.now().strftime('%H:%M:%S')}\n and we are almost closing!") if verbose else None
    writer.close()
    print(f"-> It's {datetime.now().strftime('%H:%M:%S')}\n and we've finished!") if verbose else None

    # Print stats
    if verbose:
        _show_stats([0,0,0], input_file, output_file)

def check_condition(tags, filter, pprint=False):
    for t in tags:
        if t.k in filter.keys():
            if (not filter.get(t.k)) or (filter.get(t.k) and t.v in filter.get(t.k)):
                    return True
    return False

def check_condition_relations(tags, filter1, filter2, pprint=False):
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

# class TagFilter(osmium.SimpleHandler):
#     def __init__(self, writer, filter_n, filter_w, filter_r):
#         super().__init__()
#         self.writer = writer
#         self.filter_n = filter_n
#         self.filter_w = filter_w
#         self.filter_r = filter_r
#         self.n_n = 0
#         self.n_w = 0
#         self.n_r = 0
    
#     def node(self, n):
#         tags = {tag.k: tag.v for tag in n.tags if tag.k in self.filter_n.keys()}
#         for k, v in tags.items():
#             if self.filter_n.get(k):
#                 if len(self.filter_n.get(k))==0 or v in self.filter_n.get(k):
#                     self.writer.add_node(n)
#                     self.n_n += 1
#                     return

#     def way(self, w):
#         tags = {tag.k: tag.v for tag in w.tags if tag.k in self.filter_w.keys()}
#         for k, v in tags.items():
#             if self.filter_w.get(k):
#                 if len(self.filter_w.get(k))==0 or v in self.filter_w.get(k):
#                     self.writer.add_way(w)
#                     self.n_w += 1
#                     return
    
#     def relation(self, r):
#         tags = {tag.k: tag.v for tag in r.tags if tag.k in self.filter_r.keys()}
#         for k, v in tags.items():
#             if self.filter_r.get(k):
#                 if len(self.filter_r.get(k))==0 or v in self.filter_r.get(k):
#                     self.writer.add_relation(r)
#                     self.n_r += 1
#                     return

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

# def tag_filter_with_pyosmium(input_file: str, output_file: str, filter_file: str):
#     # Compute the filters
#     full_filter_n, full_filter_w, full_filter_r = parse_filter_expression(filter_file)    
    
#     # Initialize the writer
#     writer = osmium.BackReferenceWriter(outfile=output_file, ref_src=input_file, overwrite=True, relation_depth=0)

#     # Perform the filtering
#     print(f"-> Getting elems \n and it's {datetime.now().strftime('%H:%M:%S')}") if verbose else None
#     handler = TagFilter(writer, full_filter_n, full_filter_w, full_filter_r)
#     handler.apply_file(input_file)
#     n_objects = [handler.n_n, handler.n_w, handler.n_r]
#     writer.close()
#     print(f"-> It's {datetime.now().strftime('%H:%M:%S')}\n and we've finished!") if verbose else None

#     # Print stats
#     if verbose:
#         _show_stats(n_objects, input_file, output_file)


if __name__ == "__main__":
    # Configuration
    input_file = Path("data_local/input_service/bologna-area.osm.pbf")
    output_file = Path("data/input_service/bologna-area-filtered.osm.pbf")
    filter_file = Path("data/input_service/filter_expression.sh")

    tag_filter_with_pyosmium2(str(input_file), str(output_file), str(filter_file))