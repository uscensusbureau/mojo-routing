# Python API

Official Source GitHub repository: [link](https://github.com/Project-OSRM/osrm-backend/blob/master/docs/python/api.md)

The Python bindings provide access to OSRM's routing services through the `osrm` package. Install with `pip install osrm-bindings`.

## OSRM

The `OSRM` class is the main entry point. It requires a `.osrm.*` dataset prepared by the OSRM toolchain.

```python
import osrm

# From file
engine = osrm.OSRM("path/to/data.osrm")

# With keyword arguments
engine = osrm.OSRM(
    storage_config="path/to/data.osrm",
    algorithm="CH",                      # or "MLD"
    use_shared_memory=False,
    max_locations_trip=3,
    max_locations_viaroute=3,
    max_locations_distance_table=3,
    max_locations_map_matching=3,
    max_results_nearest=1,
    max_alternatives=1,
    default_radius="unlimited",
)

# Using shared memory (requires osrm-datastore)
engine = osrm.OSRM(use_shared_memory=True)
```

### Parameters

- **`storage_config`** `str` - Path to the `.osrm` dataset.
- **`algorithm`** `str` - Routing algorithm: `"CH"` or `"MLD"`. Default: `"CH"`.
- **`use_shared_memory`** `bool` - Connect to shared memory datastore. Default: `True`.
- **`dataset_name`** `str` - Named shared memory dataset (requires `osrm-datastore --dataset_name`).
- **`memory_file`** `str` - **Deprecated.** Equivalent to `use_mmap=True`.
- **`use_mmap`** `bool` - Memory-map files instead of loading into RAM.
- **`max_locations_trip`** `int` - Max locations in trip queries.
- **`max_locations_viaroute`** `int` - Max locations in route queries.
- **`max_locations_distance_table`** `int` - Max locations in table queries.
- **`max_locations_map_matching`** `int` - Max locations in match queries.
- **`max_results_nearest`** `int` - Max results in nearest queries.
- **`max_alternatives`** `int` - Max alternative routes.
- **`default_radius`** `float | "unlimited"` - Default search radius in meters.
- **`max_radius_map_matching`** `float` - Maximum search radius used during map matching.
- **`verbosity`** `str` - Log verbosity level (e.g. `"INFO"`, `"WARNING"`, `"ERROR"`).

### Services

All service methods take a parameters object and return a dict-like `Object`:

```python
result = engine.Route(route_params)
print(result["routes"])
print(result["waypoints"])
```

## Route

Finds the fastest route between two or more coordinates.

```python
params = osrm.RouteParameters(
    coordinates=[(7.41337, 43.72956), (7.41546, 43.73077)],
    steps=True,
    alternatives=2,
    annotations=["speed", "duration"],
    geometries="geojson",
    overview="full",
)
result = engine.Route(params)
```

### RouteParameters

Inherits all [BaseParameters](#baseparameters).

- **`steps`** `bool` - Return route steps for each leg. Default: `False`.
- **`alternatives`** `bool` - Whether to search for alternative routes (set automatically when `number_of_alternatives > 0`).
- **`number_of_alternatives`** `int` - Number of alternative routes to search for. Default: `0`.
- **`annotations`** `list[str]` - Additional metadata (constructor arg). Maps to the `annotations_type` property. Values: `"none"`, `"duration"`, `"nodes"`, `"distance"`, `"weight"`, `"datasources"`, `"speed"`, `"all"`. Default: `[]`.
- **`geometries`** `str` - Geometry format: `"polyline"`, `"polyline6"`, `"geojson"`. Default: `"polyline"`.
- **`overview`** `str` - Overview geometry: `"simplified"`, `"full"`, `"false"`. Default: `"simplified"`.
- **`continue_straight`** `bool | None` - Force route to continue straight at waypoints.
- **`waypoints`** `list[int]` - Indices of coordinates to treat as waypoints. Must include first and last.

### Route Response

Returns an `Object` (dict-like) with the following fields:

- **`code`** `str` - `"Ok"` on success. See [Response Codes](#response-codes).
- **`waypoints`** `list[Waypoint]` - Snapped input coordinates. See [Waypoint](#waypoint).
- **`routes`** `list[Route]` - Ordered list of routes, best first.

**Route object:**

| Field | Type | Description |
|-------|------|-------------|
| `distance` | `float` | Total route distance in meters. |
| `duration` | `float` | Estimated travel time in seconds. |
| `geometry` | `str \| object` | Encoded geometry of the route. Format depends on `geometries` parameter. |
| `weight` | `float` | Internal routing weight. |
| `weight_name` | `str` | Weighting used (e.g. `"routability"`). |
| `legs` | `list[RouteLeg]` | One leg per waypoint pair. See [RouteLeg](#routeleg). |

---

## Table

Computes duration/distance matrices between coordinates.

```python
params = osrm.TableParameters(
    coordinates=[(7.41337, 43.72956), (7.41546, 43.73077), (7.41862, 43.73216)],
    sources=[0],
    destinations=[1, 2],
    annotations=["duration", "distance"],
)
result = engine.Table(params)
```

### TableParameters

Inherits all [BaseParameters](#baseparameters).

- **`sources`** `list[int]` - Indices of source coordinates. Default: all.
- **`destinations`** `list[int]` - Indices of destination coordinates. Default: all.
- **`annotations`** `list[str]` - `"duration"`, `"distance"`, `"all"`. Default: `["duration"]`.
- **`fallback_speed`** `float` - Speed for crow-flies fallback when no route found.
- **`fallback_coordinate_type`** `str` - `"input"` or `"snapped"`.
- **`scale_factor`** `float` - Scales duration values. Default: `1.0`.

### Table Response

Returns an `Object` with the following fields:

- **`code`** `str` - `"Ok"` on success.
- **`sources`** `list[Waypoint]` - Snapped source coordinates. See [Waypoint](#waypoint).
- **`destinations`** `list[Waypoint]` - Snapped destination coordinates.
- **`durations`** `list[list[float | None]]` - 2D matrix `[source][destination]` of travel times in seconds. `null` if no route found and no `fallback_speed` was set.
- **`distances`** `list[list[float | None]]` - 2D matrix `[source][destination]` of distances in meters. Only present when `"distance"` is in `annotations`.

---

## Nearest

Finds the nearest street segment for a coordinate.

```python
params = osrm.NearestParameters(
    coordinates=[(7.41337, 43.72956)],
    number_of_results=3,
)
result = engine.Nearest(params)
```

### NearestParameters

Inherits all [BaseParameters](#baseparameters).

- **`number_of_results`** `int` - Number of nearest segments to return. Default: `1`.

### Nearest Response

Returns an `Object` with the following fields:

- **`code`** `str` - `"Ok"` on success.
- **`waypoints`** `list[NearestWaypoint]` - Nearest street segments.

**NearestWaypoint** extends the base [Waypoint](#waypoint) with:

| Field | Type | Description |
|-------|------|-------------|
| `nodes` | `list[float]` | IDs of the two nodes of the matched edge on the network graph. |

---

## Match

Snaps noisy GPS traces to the road network.

```python
params = osrm.MatchParameters(
    coordinates=[(7.41337, 43.72956), (7.41546, 43.73077), (7.41862, 43.73216)],
    timestamps=[1424684612, 1424684616, 1424684620],
    radiuses=[5.0, 5.0, 5.0],
    annotations=["speed"],
    geometries="geojson",
)
result = engine.Match(params)
```

### MatchParameters

Inherits all [RouteParameters](#routeparameters) and [BaseParameters](#baseparameters).

- **`timestamps`** `list[int]` - UNIX timestamps for each coordinate.
- **`gaps`** `str` - Gap handling: `"split"` or `"ignore"`. Default: `"split"`.
- **`tidy`** `bool` - Remove duplicates. Default: `False`.
- **`waypoints`** `list[int]` - Inherited from [RouteParameters](#routeparameters). Indices of coordinates to treat as waypoints.

### Match Response

Returns an `Object` with the following fields:

- **`code`** `str` - `"Ok"` on success.
- **`tracepoints`** `list[Tracepoint | None]` - One entry per input coordinate. `null` if the point could not be matched.
- **`matchings`** `list[Matching]` - Matched route segments.

**Tracepoint** extends the base [Waypoint](#waypoint) with:

| Field | Type | Description |
|-------|------|-------------|
| `matchings_index` | `float` | Index into `matchings` that this tracepoint belongs to. |
| `waypoint_index` | `float` | Index of this tracepoint within its matching. |
| `alternatives_count` | `float` | Number of alternative matchings for this point. |

**Matching** extends the base [Route](#route-response) object with:

| Field | Type | Description |
|-------|------|-------------|
| `confidence` | `float` | Confidence score of the match (0–1). Higher is more confident. |

---

## Trip

Solves the Traveling Salesman Problem for the given coordinates.

```python
params = osrm.TripParameters(
    coordinates=[(7.41337, 43.72956), (7.41546, 43.73077), (7.41862, 43.73216)],
    source="first",
    destination="last",
    roundtrip=True,
    annotations=["duration"],
    geometries="geojson",
)
result = engine.Trip(params)
```

### TripParameters

Inherits all [RouteParameters](#routeparameters) and [BaseParameters](#baseparameters).

> **Note:** `TripParameters` uses `alternatives` (int, default `0`) as its constructor argument for alternative count — not `number_of_alternatives` as in `RouteParameters`.

- **`source`** `str` - `"any"` or `"first"`. Default: `"any"`.
- **`destination`** `str` - `"any"` or `"last"`. Default: `"any"`.
- **`roundtrip`** `bool` - Return to first location. Default: `True`.

### Trip Response

Returns an `Object` with the following fields:

- **`code`** `str` - `"Ok"` on success.
- **`trips`** `list[Route]` - Optimized trip routes. Each has the same structure as a [Route response](#route-response) object.
- **`waypoints`** `list[TripWaypoint]` - Snapped input coordinates.

**TripWaypoint** extends the base [Waypoint](#waypoint) with:

| Field | Type | Description |
|-------|------|-------------|
| `trips_index` | `float` | Index into `trips` that this waypoint belongs to. |
| `waypoint_index` | `float` | Position of this waypoint within its trip. |

---

## Tile

Generates vector tiles with internal routing graph data.

```python
params = osrm.TileParameters(x=17059, y=11948, z=15)
result = engine.Tile(params)  # returns bytes
```

### TileParameters

- **`x`** `int` - Tile x coordinate.
- **`y`** `int` - Tile y coordinate.
- **`z`** `int` - Tile zoom level.

### Tile Response

Returns raw `bytes` in [Mapbox Vector Tile](https://docs.mapbox.com/vector-tiles/specification/) (MVT) format. Contains internal routing graph edges and nodes useful for visualising the road network. Unlike other services, this does **not** return a JSON `Object`.

```python
params = osrm.TileParameters(x=17059, y=11948, z=15)
tile_bytes = engine.Tile(params)  # raw bytes, not a dict
```

---

## Shared Response Objects

These nested objects appear in the responses of multiple services.

### Waypoint

A coordinate snapped to the street network. Present in Route, Table, Nearest, Match, and Trip responses.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Name of the road the coordinate was snapped to. Empty string if unnamed. |
| `location` | `[float, float]` | `[longitude, latitude]` of the snapped point. |
| `distance` | `float` | Distance in meters from the input coordinate to the snapped location. |
| `hint` | `str` | Base64-encoded hint for faster subsequent requests. Pass back via `hints` parameter. |

### RouteLeg

One leg of a route, representing travel between two consecutive waypoints.

| Field | Type | Description |
|-------|------|-------------|
| `distance` | `float` | Distance traveled in meters. |
| `duration` | `float` | Estimated travel time in seconds. |
| `weight` | `float` | Internal routing weight for this leg. |
| `summary` | `str` | Summary of the leg (major road names). May be empty. |
| `steps` | `list[RouteStep]` | Turn-by-turn steps. Empty unless `steps=True`. See [RouteStep](#routestep). |
| `annotation` | `Annotation \| None` | Per-node metadata. Only present when `annotations` are requested. See [Annotation](#annotation). |

### RouteStep

A single maneuver step within a leg. Only present when `steps=True`.

| Field | Type | Description |
|-------|------|-------------|
| `distance` | `float` | Distance of this step in meters. |
| `duration` | `float` | Duration of this step in seconds. |
| `geometry` | `str \| object` | Geometry of this step (format matches `geometries` parameter). |
| `weight` | `float` | Routing weight for this step. |
| `name` | `str` | Name of the road on this step. |
| `ref` | `str` | Road reference number (e.g. `"I-95"`). May be absent. |
| `pronunciation` | `str` | Phonetic pronunciation of the road name. May be absent. |
| `destinations` | `str` | Signposted destinations. May be absent. |
| `exits` | `str` | Signposted exit numbers. May be absent. |
| `mode` | `str` | Travel mode (e.g. `"driving"`, `"ferry"`). |
| `driving_side` | `str` | `"left"` or `"right"` depending on traffic rules. |
| `maneuver` | `StepManeuver` | The maneuver at the start of this step. See [StepManeuver](#stepmaneuver). |
| `intersections` | `list[Intersection]` | All intersections along this step. See [Intersection](#intersection). |
| `rotary_name` | `str` | Name of the rotary/roundabout. Only for `"rotary"` / `"roundabout"` maneuver types. |
| `rotary_pronunciation` | `str` | Phonetic pronunciation of the rotary name. |

### StepManeuver

Describes the action required at the beginning of a `RouteStep`.

| Field | Type | Description |
|-------|------|-------------|
| `location` | `[float, float]` | `[longitude, latitude]` of the maneuver. |
| `bearing_before` | `int` | Bearing (0–359°) approaching the maneuver. |
| `bearing_after` | `int` | Bearing (0–359°) leaving the maneuver. |
| `type` | `str` | Maneuver type. See values below. |
| `modifier` | `str` | Direction modifier. See values below. May be absent. |
| `exit` | `int` | Exit number for roundabout/rotary maneuvers. May be absent. |

**`type` values:** `"depart"`, `"arrive"`, `"turn"`, `"new name"`, `"merge"`, `"on ramp"`, `"off ramp"`, `"fork"`, `"end of road"`, `"continue"`, `"roundabout"`, `"rotary"`, `"roundabout turn"`, `"notification"`, `"exit roundabout"`, `"exit rotary"`

**`modifier` values:** `"uturn"`, `"sharp right"`, `"right"`, `"slight right"`, `"straight"`, `"slight left"`, `"left"`, `"sharp left"`

### Intersection

An intersection encountered along a `RouteStep`.

| Field | Type | Description |
|-------|------|-------------|
| `location` | `[float, float]` | `[longitude, latitude]` of the intersection. |
| `bearings` | `list[int]` | All road bearings available at the intersection. |
| `entry` | `list[bool]` | Whether each road in `bearings` is drivable as an entry. |
| `classes` | `list[str]` | Road classes (e.g. `"motorway"`, `"toll"`). May be absent. |
| `in` | `int` | Index into `bearings` for the road used to arrive. May be absent. |
| `out` | `int` | Index into `bearings` for the road used to depart. May be absent. |
| `lanes` | `list[LaneInfo]` | Lane information. Only present when lane guidance is available. See [LaneInfo](#laneinfo). |

### LaneInfo

Lane guidance at an intersection.

| Field | Type | Description |
|-------|------|-------------|
| `indications` | `list[str]` | Turn directions this lane allows (e.g. `["left", "straight"]`). |
| `valid` | `bool` | Whether this lane can be used for the current maneuver. |

### Annotation

Per-segment metadata along a leg. Only present when `annotations` are requested.

| Field | Type | Description |
|-------|------|-------------|
| `duration` | `list[float]` | Travel time in seconds for each segment between consecutive nodes. |
| `distance` | `list[float]` | Distance in meters for each segment. |
| `speed` | `list[float]` | Speed in m/s for each segment. |
| `weight` | `list[float]` | Routing weight for each segment. |
| `nodes` | `list[int]` | OSM node IDs for each node along the route (length = segments + 1). |
| `datasources` | `list[int]` | Index of the datasource used for each segment's speed. |

Each array has length equal to the number of road segments in the leg (one less than the number of nodes).

### Response Codes

The `code` field is present in all service responses.

| Value | Meaning |
|-------|---------|
| `"Ok"` | Request succeeded. |
| `"InvalidUrl"` | URL string is invalid. |
| `"InvalidService"` | Service name is invalid. |
| `"InvalidVersion"` | Version is not found. |
| `"InvalidOptions"` | Options are invalid. |
| `"InvalidQuery"` | The query string is invalid. |
| `"InvalidValue"` | The supplied argument is invalid. |
| `"NoSegment"` | One of the supplied input coordinates could not snap to a street segment. |
| `"TooBig"` | The request size violates a server-side limit. |
| `"NoRoute"` | No route found. |
| `"NoTable"` | No route found for the table query. |
| `"NotImplemented"` | Feature is not implemented. |
| `"NoTrips"` | No trips could be computed. |

## BaseParameters

Shared parameters inherited by Nearest, Table, Route, Match, and Trip.

- **`coordinates`** `list[tuple[float, float]]` - List of `(longitude, latitude)` pairs.
- **`hints`** `list[str | None]` - Base64-encoded hints from previous requests.
- **`radiuses`** `list[float | None]` - Search radius per coordinate in meters. `None` for unlimited.
- **`bearings`** `list[tuple[int, int] | None]` - `(bearing, range)` pairs in degrees. `None` for unrestricted.
- **`approaches`** `list[str | None]` - `"curb"`, `"unrestricted"`, or `None`.
- **`generate_hints`** `bool` - Include hints in response. Default: `True`.
- **`exclude`** `list[str]` - Road classes to avoid (e.g. `["motorway"]`).
- **`snapping`** `str` - `"default"` or `"any"`. Default: `"default"`.
- **`format`** `str | None` - Response format. Currently only `"json"` is supported.
- **`skip_waypoints`** `bool` - Removes waypoints from the response. Default: `False`.

## Types

### Coordinate

```python
coord = osrm.Coordinate((7.41337, 43.72956))
print(coord.lon, coord.lat)
```

### Bearing

```python
bearing = osrm.Bearing((200, 180))
print(bearing.bearing, bearing.range)
```

### Object / Array

Service results are returned as `Object` (dict-like) and `Array` (list-like) wrappers around OSRM's internal JSON types. They support `[]`, `len()`, `in`, and iteration.

```python
result = engine.Route(params)
for route in result["routes"]:
    print(route["distance"], route["duration"])
```

### Enum / Type Classes

OSRM uses typed wrapper classes for string-valued parameters. Each accepts a plain string in the constructor and returns a string from `repr()`. Some annotation types additionally support bitwise `|` to combine values.

| Class | Valid string values |
|-------|---------------------|
| `SnappingType` | `"default"`, `"any"` |
| `OutputFormatType` | `"json"` |
| `TableFallbackCoordinateType` | `"input"`, `"snapped"` |
| `TableAnnotationsType` | `"none"`, `"duration"`, `"distance"`, `"all"` |
| `RouteGeometriesType` | `"polyline"`, `"polyline6"`, `"geojson"` |
| `RouteOverviewType` | `"simplified"`, `"full"`, `"false"` |
| `RouteAnnotationsType` | `"none"`, `"duration"`, `"nodes"`, `"distance"`, `"weight"`, `"datasources"`, `"speed"`, `"all"` |
| `MatchGapsType` | `"split"`, `"ignore"` |
| `TripSourceType` | `"any"`, `"first"` |
| `TripDestinationType` | `"any"`, `"last"` |

`TableAnnotationsType` and `RouteAnnotationsType` support the `|` operator to combine flags:

```python
ann = osrm.RouteAnnotationsType("duration") | osrm.RouteAnnotationsType("distance")
```

## CLI

The package also installs OSRM command-line tools, accessible via `python -m osrm`:

```bash
python -m osrm extract data.osm.pbf -p profiles/car.lua
python -m osrm contract data.osrm
python -m osrm partition data.osrm
python -m osrm customize data.osrm
python -m osrm datastore data.osrm
python -m osrm routed data.osrm
```