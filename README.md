# OSRM Python Bindings

A Python usage layer on top of [`osrm-bindings`](https://pypi.org/project/osrm-bindings/) for road-network routing. [OSRM (Open Source Routing Machine)](https://project-osrm.org/) is a high-performance routing engine that computes routes, distance/duration matrices, map-matching, and more against a preprocessed road network.

**Requirements:** Python ≥ 3.12 · [`osrm-bindings`](https://pypi.org/project/osrm-bindings/) · [`python-dotenv`](https://pypi.org/project/python-dotenv/)

---

## Setup & Installation

```bash
# Single setup script
bash setup/setup.sh
```

Create a `.env` file in the project root:


---

## Quick Start

The examples below mirror [`routing_examples.py`](routing_examples.py).

```python
import os
import ast
import osrm
from dotenv import load_dotenv

load_dotenv()
osrm_file = os.getenv("MAP_LOCATION")

# Initialize the engine
osrm_py = osrm.OSRM(
    storage_config=osrm_file,
    algorithm='CH',
    use_shared_memory=False,       # Required when loading from file (not osrm-datastore)
    use_mmap=True,                 # Memory-map the dataset — avoids loading entire map into RAM
    max_locations_distance_table=5000,
    max_locations_trip=500,
)
```

### OD Cost Matrix (Table)

```python
route_params = osrm.TableParameters(
    coordinates=[[-76.710840, 39.254750], [-76.760627, 39.284319], [-76.690120, 39.245220]],
    sources=[0, 1],
    destinations=[1, 2],
    annotations=["duration", "distance"],  # duration in seconds, distance in meters
)

table_result = osrm_py.Table(route_params)

# Results are custom C++ objects — convert to a Python dict before use
table_result = ast.literal_eval(str(table_result)) if table_result else None
print(table_result)
```

See [`api.md`](api.md) for all available services (Route, Nearest, Match, Trip, Tile).

---

> **Disclaimer:** All coordinate examples used throughout this documentation and example scripts are sourced from publicly accessible locations — either publicly listed state park areas (e.g., Maryland state parks) or coordinates from the [OSRM public documentation](https://project-osrm.org/docs/v5.24.0/api/). No private, sensitive, or personally identifiable location data is used.

## Important Usage Nuances

### 1. Coordinates are `[longitude, latitude]` — not `[lat, lon]`

All coordinate inputs follow GeoJSON convention: **longitude first, then latitude**. This is the opposite of what many mapping tools display.

```python
# Correct: [lon, lat]
coordinates=[
    [-77.4688, 39.6225],  # Cunningham Falls State Park, Catoctin Mountains
    [-75.4408, 38.1294],  # Pocomoke River State Park, Lower Eastern Shore
]

# Wrong: [lat, lon] — will silently produce incorrect routes
coordinates=[[39.6225, -77.4688], ...]
```

### 2. Results are custom objects — convert with `ast.literal_eval`

OSRM service methods return a custom C++ wrapper object, not a native Python dict. You must convert it before you can work with it like a dictionary or serialize it to JSON:

```python
result = osrm_py.Table(params)
result = ast.literal_eval(str(result)) if result else None
# Now result is a standard Python dict
print(result["durations"])
```

### 3. File-based loading requires `use_shared_memory=False`

The default is `use_shared_memory=True`, which expects a running `osrm-datastore` process. When loading directly from a `.osrm` file, you **must** set it to `False`:

```python
osrm.OSRM(storage_config="path/to/data.osrm", use_shared_memory=False)
```

### 4. Use `use_mmap=True` for large datasets

Without memory-mapping, OSRM loads the entire dataset into RAM. For large maps (e.g. all of North America), always enable memory-mapping:

```python
osrm.OSRM(..., use_mmap=True)
```

### 5. CH and MLD require separate datasets

You cannot use the same preprocessed dataset for both the Contraction Hierarchies (`CH`) and Multi-Level Dijkstra (`MLD`) algorithms. Build and maintain separate `.osrm` files for each algorithm you need.

### 6. Each profile requires its own dataset

A dataset built with `car.lua` cannot be used with `foot.lua` or `bicycle.lua`. Each routing profile (available in `profiles/`) must be built into its own dataset:

| Profile | Use case |
|---|---|
| `car.lua` | Driving routes |
| `bicycle.lua` | Cycling routes |
| `foot.lua` | Walking routes |

---

## Road Network Data

The base road network (`.osm.pbf`) is sourced from [Geofabrik](https://download.geofabrik.de/north-america.html) and preprocessed using the OSRM toolchain into `.osrm` files stored in `data/`.

**Current dataset:** Full North America (including Alaska), built with the `CH` algorithm and `car.lua` profile.

Additional profiles for building alternative datasets are in `profiles/`: `car.lua`, `bicycle.lua`, `foot.lua`, `rasterbot.lua`, and others.

Command used to build the dataset:

```bash
osrm-extract -p profiles/car.lua data/us-260611.osm.pbf
# Contract the extracted data for the CH algorithm (contraction hierarchies, must for large road networks)
osrm-contract data/us-260611.osrm
```
On a laptop workstation with 64 GB RAM, it take about 10 hours to build the full North America. This is a very RAM and CPU intensive processing.

---


Follow the following steps to create a portable standalone python venv.
```bash
# 1. Create the virtual environment and download a standalone Python version
uv venv --python 3.13

# 2. Install your required dependencies
uv pip install <package-name> --target .venv/lib/site-packages

# Force the environment to use relative paths so it is relocatable
uv venv --relocatable ./venv

./.venv/bin/python your_script.py

```

---

## Calling from Stata (Python Integration)

Stata 16+ includes a built-in Python integration that lets you run Python code inline with `python:` blocks. You can call any of the `osrm_routing` service functions directly from a `.do` file.

### Prerequisites

1. **Stata ≥ 16** with Python integration enabled.
2. **Python ≥ 3.12** configured in Stata:
   ```stata
   python set exec "/apps/anaconda/bin/python", permanently
   ```
3. **`osrm-bindings`** installed in that Python environment:
   ```bash
   pip install osrm-bindings
   ```
4. A preprocessed `.osrm` dataset (see [Road Network Data](#road-network-data)).

### Adding the module to Stata's Python path

At the top of your `.do` file, add the repository directory to `sys.path` so Python can find `osrm_routing`:

```stata
python:
import sys
sys.path.insert(0, "C:/path/to/ire-wario")
end
```

You only need to do this once per Stata session.

---

### Table — OD Cost Matrix

Returns a duration/distance matrix between a set of source and destination coordinates.

```stata
python:
import sys, json
sys.path.insert(0, "C:/path/to/ire-wario")
from osrm_routing import osrm_table
import sfi

engine_cfg = {"storage_config": "C:/path/to/data.osrm"}

coords = [
    [-76.710840, 39.254750],   # index 0 — source
    [-76.760627, 39.284319],   # index 1 — destination
    [-76.690120, 39.245220],   # index 2 — destination
]

result_json = osrm_table(
    coordinates=coords,
    sources=[0],
    destinations=[1, 2],
    annotations=["duration", "distance"],
    engine_config=engine_cfg,
)

result = json.loads(result_json)
# durations[i][j] is seconds from source i to destination j
print(result["durations"])
# Pass first duration back to Stata as a local macro
sfi.Macro.setLocal("dur_0_1", str(result["durations"][0][0]))
end

display "Duration (s): `dur_0_1'"
```

---

### Route

Returns turn-by-turn directions and geometry between an ordered list of waypoints.

```stata
python:
import sys, json
sys.path.insert(0, "C:/path/to/ire-wario")
from osrm_routing import osrm_route
import sfi

engine_cfg = {"storage_config": "C:/path/to/data.osrm"}

result_json = osrm_route(
    coordinates=[
        [-76.710840, 39.254750],
        [-76.760627, 39.284319],
    ],
    steps=False,
    overview="simplified",
    geometries="geojson",
    engine_config=engine_cfg,
)

result = json.loads(result_json)
route = result["routes"][0]
duration_s  = route["duration"]   # seconds
distance_m  = route["distance"]   # meters

sfi.Macro.setLocal("route_duration", str(duration_s))
sfi.Macro.setLocal("route_distance", str(distance_m))
end

display "Duration (s): `route_duration'  |  Distance (m): `route_distance'"
```

---

### Nearest

Snaps a coordinate to the nearest road segment and returns candidate roads.

```stata
python:
import sys, json
sys.path.insert(0, "C:/path/to/ire-wario")
from osrm_routing import osrm_nearest
import sfi

engine_cfg = {"storage_config": "C:/path/to/data.osrm"}

result_json = osrm_nearest(
    coordinates=[[-76.710840, 39.254750]],
    number_of_results=1,
    engine_config=engine_cfg,
)

result = json.loads(result_json)
waypoint = result["waypoints"][0]
snapped_lon = waypoint["location"][0]
snapped_lat = waypoint["location"][1]

sfi.Macro.setLocal("snapped_lon", str(snapped_lon))
sfi.Macro.setLocal("snapped_lat", str(snapped_lat))
end

display "Snapped location: `snapped_lon', `snapped_lat'"
```

---

### Match — Map Matching

Matches a sequence of GPS coordinates (with optional timestamps) to the road network.

```stata
python:
import sys, json
sys.path.insert(0, "C:/path/to/ire-wario")
from osrm_routing import osrm_match
import sfi

engine_cfg = {"storage_config": "C:/path/to/data.osrm"}

result_json = osrm_match(
    coordinates=[
        [-76.710840, 39.254750],
        [-76.730000, 39.265000],
        [-76.760627, 39.284319],
    ],
    timestamps=[1700000000, 1700000060, 1700000120],  # UNIX seconds
    tidy=True,
    overview="simplified",
    geometries="geojson",
    engine_config=engine_cfg,
)

result = json.loads(result_json)
matched_distance = result["matchings"][0]["distance"]  # meters

sfi.Macro.setLocal("matched_dist", str(matched_distance))
end

display "Matched route distance (m): `matched_dist'"
```

---

### Trip — Travelling Salesman

Finds an efficient round-trip (or open-ended trip) visiting all supplied coordinates.

```stata
python:
import sys, json
sys.path.insert(0, "C:/path/to/ire-wario")
from osrm_routing import osrm_trip
import sfi

engine_cfg = {"storage_config": "C:/path/to/data.osrm"}

result_json = osrm_trip(
    coordinates=[
        [-76.710840, 39.254750],
        [-76.760627, 39.284319],
        [-76.690120, 39.245220],
    ],
    source="first",
    destination="last",
    roundtrip=False,
    overview="simplified",
    engine_config=engine_cfg,
)

result = json.loads(result_json)
trip_duration = result["trips"][0]["duration"]   # seconds
trip_distance = result["trips"][0]["distance"]   # meters

sfi.Macro.setLocal("trip_duration", str(trip_duration))
sfi.Macro.setLocal("trip_distance", str(trip_distance))
end

display "Trip duration (s): `trip_duration'  |  Trip distance (m): `trip_distance'"
```

---

### Writing results directly to a file

If you prefer to write the JSON to disk (e.g. to load with `import delimited` or `jsonio`), pass `output_filepath`:

```stata
python:
import sys
sys.path.insert(0, "C:/path/to/ire-wario")
from osrm_routing import osrm_table

osrm_table(
    coordinates=[[-76.710840, 39.254750], [-76.760627, 39.284319]],
    annotations=["duration", "distance"],
    engine_config={"storage_config": "C:/path/to/data.osrm"},
    output_filepath="C:/path/to/output/table_result.json",
)
end
```

---

## API Reference

See [`api.md`](api.md) for full documentation of the `OSRM` class and all service methods: `Route`, `Table`, `Nearest`, `Match`, `Trip`, and `Tile`.
