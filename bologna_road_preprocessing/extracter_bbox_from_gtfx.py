import pandas as pd

# Load stops.txt
stops = pd.read_csv("data/gommagtfsbo_20250513/stops.txt")

# Ensure required columns exist
if 'stop_lat' not in stops or 'stop_lon' not in stops:
    raise ValueError("stops.txt must contain 'stop_lat' and 'stop_lon' columns")

# Calculate bounding box
min_lat = stops['stop_lat'].min()
max_lat = stops['stop_lat'].max()
min_lon = stops['stop_lon'].min()
max_lon = stops['stop_lon'].max()

# Bounding box format: (min_lon, min_lat, max_lon, max_lat)
bounding_box = (float(min_lon), 
                float(min_lat), 
                float(max_lon), 
                float(max_lat))
print("Bounding Box:", bounding_box)
# (10.79511592, 44.09166617, 12.31057532, 44.8521224)
