import osmium
from pathlib import Path
import sys
import os
sys.path.append(f"{os.path.expanduser('.')}/src")
from params import verbose


class AreaFilter(osmium.SimpleHandler):
    def __init__(self, writer, bbox):
        super().__init__()
        self.writer = writer
        self.min_lon, self.min_lat, self.max_lon, self.max_lat = bbox

    def node(self, n):
        if not n.location.valid():
            return
        lon, lat = n.location.lon, n.location.lat
        if self.min_lon <= lon <= self.max_lon and self.min_lat <= lat <= self.max_lat:
            self.writer.add_node(n)

def _show_file_sizes(input_file: str, output_file: str):
    # Show file sizes
    original_size = Path(input_file).stat().st_size / (1024 * 1024)
    filtered_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"Original size: {original_size:.2f} MB → Filtered size: {filtered_size:.2f} MB")

def cut_area_with_bbox(input_file: str, output_file: str, bbox):
    writer = osmium.SimpleWriter(output_file, overwrite=True)
    handler = AreaFilter(writer, bbox)
    handler.apply_file(input_file, locations=True)
    writer.close()
    if verbose:
        _show_file_sizes(input_file, output_file)


if __name__ == "__main__":
    data_folder = Path("./data/input_service")
    input_file = str(data_folder / "nord-est-latest.osm.pbf")
    output_file = str(data_folder / "bologna-area.osm.pbf")
    bbox = [10.734269464357556,43.96629819030445,12.139133497965453,44.91004596649926]
    cut_area_with_bbox(input_file, output_file, bbox)