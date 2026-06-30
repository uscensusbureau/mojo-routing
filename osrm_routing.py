"""
Low level cli calls to various osrm services.

Usage:
    python osrm_routing.py --input_coordinates coords.json --input_config params.json \
        --osrm_service table [--output_filepath ./output/result.json] [--engine_config engine.json]
"""

import argparse
import ast
import json
import platform
import sys

import osrm


DEFAULT_ENGINE_CONFIG = {
    "storage_config": "data/your_data.osrm",
    "algorithm": "CH",
    "use_shared_memory": False,
    "use_mmap": True,
    "max_results_nearest": 1,
    "max_alternatives": 1,
    "default_radius": "unlimited",
}


def load_json_file(path: str, label: str) -> dict | list:
    """Load and return JSON from *path*, raising SystemExit on failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        sys.exit(f"Error: {label} file not found: {path!r}")
    except json.JSONDecodeError as exc:
        sys.exit(f"Error: {label} file is not valid JSON ({path!r}): {exc}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Low-level CLI for OSRM routing services (table, route, nearest, match, trip).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--engine_config",
        metavar="FILE",
        default=None,
        help="Optional JSON file with osrm.OSRM() engine parameters. "
             "Falls back to built-in defaults when omitted.",
    )
    parser.add_argument(
        "--input_coordinates",
        metavar="FILE",
        required=True,
        help="JSON file containing a list of [longitude, latitude] coordinate pairs.",
    )
    parser.add_argument(
        "--input_config",
        metavar="FILE",
        required=True,
        help="JSON file with service-specific parameters "
             "(e.g. sources, destinations, annotations for 'table').",
    )
    parser.add_argument(
        "--output_filepath",
        metavar="FILE",
        required=False,
        default=None,
        help="File path where the result JSON will be written. "
             "If omitted, the result is printed to stdout.",
    )
    parser.add_argument(
        "--osrm_service",
        choices=["table", "route", "nearest", "match", "trip"],
        required=True,
        help="OSRM service to call.",
    )
    return parser


def _call_osrm(
    engine: "osrm.OSRM",
    method_name: str,
    params: object,
    output_filepath: str | None,
) -> str:
    """Invoke an OSRM engine method, serialize the result, and return/write it."""
    method = getattr(engine, method_name)
    try:
        raw_result = method(params)
    except Exception as exc:
        raise RuntimeError(
            f"Error calling OSRM {method_name} service: {exc}"
        ) from exc

    result = ast.literal_eval(str(raw_result)) if raw_result else {}

    if output_filepath is not None:
        with open(output_filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        return output_filepath

    return json.dumps(result)


def _build_engine(engine_config: dict | None) -> "osrm.OSRM":
    """Merge *engine_config* with defaults and return an initialised OSRM engine."""
    merged = DEFAULT_ENGINE_CONFIG.copy()
    if engine_config:
        merged.update(engine_config)
    try:
        return osrm.OSRM(**merged)
    except Exception as exc:
        raise RuntimeError(f"Error initializing OSRM engine: {exc}") from exc


def osrm_table(
    coordinates: list,
    sources: list[int] | None = None,
    destinations: list[int] | None = None,
    annotations: list[str] | None = None,
    fallback_speed: float = 3.4028234663852886e38,
    fallback_coordinate_type: str = "",
    scale_factor: float = 1.0,
    hints: list | None = None,
    radiuses: list | None = None,
    bearings: list | None = None,
    approaches: list | None = None,
    generate_hints: bool = True,
    exclude: list[str] | None = None,
    snapping: str = "",
    engine_config: dict | None = None,
    output_filepath: str | None = None,
) -> str:
    """Call the OSRM Table service.

    Args:
        coordinates: List of [longitude, latitude] pairs.
        sources: Indices into coordinates to use as sources. Defaults to all.
        destinations: Indices into coordinates to use as destinations. Defaults to all.
        annotations: Metrics to return — 'duration', 'distance', or 'all'.
        fallback_speed: Speed (m/s) used for straight-line fallback when no route exists.
        fallback_coordinate_type: 'input' or 'snapped' for fallback distance calculation.
        scale_factor: Multiplier applied to duration values.
        hints: Hints from a previous request to speed up snapping.
        radiuses: Per-coordinate search radius in metres.
        bearings: Per-coordinate bearing constraints as (bearing, range) pairs.
        approaches: Per-coordinate curb-side constraint ('curb' or 'unrestricted').
        generate_hints: Include snapping hints in the response.
        exclude: Road classes to avoid (e.g. ['motorway']).
        snapping: 'default' or 'any'.
        engine_config: OSRM engine parameters. Defaults to DEFAULT_ENGINE_CONFIG when None.
        output_filepath: Write result JSON here and return the path; or return json.dumps str.

    Returns:
        JSON string of the result, or the output file path if output_filepath was given.

    Raises:
        ValueError: On invalid inputs.
        RuntimeError: On OSRM engine or service failure.
    """
    if not isinstance(coordinates, list):
        raise ValueError("coordinates must be a list of [lon, lat] pairs.")

    params = osrm.TableParameters(
        coordinates=coordinates,
        sources=sources or [],
        destinations=destinations or [],
        annotations=annotations or [],
        fallback_speed=fallback_speed,
        fallback_coordinate_type=fallback_coordinate_type,
        scale_factor=scale_factor,
        hints=hints or [],
        radiuses=radiuses or [],
        bearings=bearings or [],
        approaches=approaches or [],
        generate_hints=generate_hints,
        exclude=exclude or [],
        snapping=snapping,
    )

    return _call_osrm(_build_engine(engine_config), "Table", params, output_filepath)


def osrm_route(
    coordinates: list,
    steps: bool = False,
    number_of_alternatives: int = 0,
    annotations: list[str] | None = None,
    geometries: str = "",
    overview: str = "",
    continue_straight: bool | None = None,
    waypoints: list[int] | None = None,
    hints: list | None = None,
    radiuses: list | None = None,
    bearings: list | None = None,
    approaches: list | None = None,
    generate_hints: bool = True,
    exclude: list[str] | None = None,
    snapping: str = "",
    engine_config: dict | None = None,
    output_filepath: str | None = None,
) -> str:
    """Call the OSRM Route service.

    Args:
        coordinates: List of [longitude, latitude] pairs.
        steps: Return turn-by-turn steps for each leg.
        number_of_alternatives: Number of alternative routes to search for.
        annotations: Per-step metadata — 'none', 'duration', 'nodes', 'distance',
            'weight', 'datasources', 'speed', or 'all'.
        geometries: Route geometry format — 'polyline', 'polyline6', or 'geojson'.
        overview: Overview geometry detail — 'simplified', 'full', or 'false'.
        continue_straight: Force straight-ahead at waypoints (no u-turns).
        waypoints: Indices of coordinates that are waypoints in the response.
        hints: Hints from a previous request to speed up snapping.
        radiuses: Per-coordinate search radius in metres.
        bearings: Per-coordinate bearing constraints as (bearing, range) pairs.
        approaches: Per-coordinate curb-side constraint.
        generate_hints: Include snapping hints in the response.
        exclude: Road classes to avoid.
        snapping: 'default' or 'any'.
        engine_config: OSRM engine parameters. Defaults to DEFAULT_ENGINE_CONFIG when None.
        output_filepath: Write result JSON here and return the path; or return json.dumps str.

    Returns:
        JSON string of the result, or the output file path if output_filepath was given.

    Raises:
        ValueError: On invalid inputs.
        RuntimeError: On OSRM engine or service failure.
    """
    if not isinstance(coordinates, list):
        raise ValueError("coordinates must be a list of [lon, lat] pairs.")

    params = osrm.RouteParameters(
        coordinates=coordinates,
        steps=steps,
        number_of_alternatives=number_of_alternatives,
        annotations=annotations or [],
        geometries=geometries,
        overview=overview,
        continue_straight=continue_straight,
        waypoints=waypoints or [],
        hints=hints or [],
        radiuses=radiuses or [],
        bearings=bearings or [],
        approaches=approaches or [],
        generate_hints=generate_hints,
        exclude=exclude or [],
        snapping=snapping,
    )

    return _call_osrm(_build_engine(engine_config), "Route", params, output_filepath)


def osrm_nearest(
    coordinates: list,
    number_of_results: int = 1,
    hints: list | None = None,
    radiuses: list | None = None,
    bearings: list | None = None,
    approaches: list | None = None,
    generate_hints: bool = True,
    exclude: list[str] | None = None,
    snapping: str = "",
    engine_config: dict | None = None,
    output_filepath: str | None = None,
) -> str:
    """Call the OSRM Nearest service.

    Args:
        coordinates: List of [longitude, latitude] pairs.
        number_of_results: Number of nearest road segments to return.
        hints: Hints from a previous request to speed up snapping.
        radiuses: Per-coordinate search radius in metres.
        bearings: Per-coordinate bearing constraints as (bearing, range) pairs.
        approaches: Per-coordinate curb-side constraint.
        generate_hints: Include snapping hints in the response.
        exclude: Road classes to avoid.
        snapping: 'default' or 'any'.
        engine_config: OSRM engine parameters. Defaults to DEFAULT_ENGINE_CONFIG when None.
        output_filepath: Write result JSON here and return the path; or return json.dumps str.

    Returns:
        JSON string of the result, or the output file path if output_filepath was given.

    Raises:
        ValueError: On invalid inputs.
        RuntimeError: On OSRM engine or service failure.
    """
    if not isinstance(coordinates, list):
        raise ValueError("coordinates must be a list of [lon, lat] pairs.")

    params = osrm.NearestParameters(
        coordinates=coordinates,
        hints=hints or [],
        radiuses=radiuses or [],
        bearings=bearings or [],
        approaches=approaches or [],
        generate_hints=generate_hints,
        exclude=exclude or [],
        snapping=snapping,
    )
    params.number_of_results = number_of_results

    return _call_osrm(_build_engine(engine_config), "Nearest", params, output_filepath)


def osrm_match(
    coordinates: list,
    timestamps: list[int] | None = None,
    gaps: str = "",
    tidy: bool = False,
    steps: bool = False,
    number_of_alternatives: int = 0,
    annotations: list[str] | None = None,
    geometries: str = "",
    overview: str = "",
    continue_straight: bool | None = None,
    waypoints: list[int] | None = None,
    hints: list | None = None,
    radiuses: list | None = None,
    bearings: list | None = None,
    approaches: list | None = None,
    generate_hints: bool = True,
    exclude: list[str] | None = None,
    snapping: str = "",
    engine_config: dict | None = None,
    output_filepath: str | None = None,
) -> str:
    """Call the OSRM Match service.

    Args:
        coordinates: List of [longitude, latitude] pairs.
        timestamps: UNIX timestamps (seconds) for each coordinate.
        gaps: How to handle timestamp gaps — 'split' or 'ignore'.
        tidy: Clean up noisy traces before matching.
        steps: Return turn-by-turn steps for each leg.
        number_of_alternatives: Number of alternative matches to search for.
        annotations: Per-step metadata.
        geometries: Route geometry format — 'polyline', 'polyline6', or 'geojson'.
        overview: Overview geometry detail — 'simplified', 'full', or 'false'.
        continue_straight: Force straight-ahead at waypoints.
        waypoints: Indices of coordinates treated as waypoints.
        hints: Hints from a previous request to speed up snapping.
        radiuses: Per-coordinate search radius in metres.
        bearings: Per-coordinate bearing constraints as (bearing, range) pairs.
        approaches: Per-coordinate curb-side constraint.
        generate_hints: Include snapping hints in the response.
        exclude: Road classes to avoid.
        snapping: 'default' or 'any'.
        engine_config: OSRM engine parameters. Defaults to DEFAULT_ENGINE_CONFIG when None.
        output_filepath: Write result JSON here and return the path; or return json.dumps str.

    Returns:
        JSON string of the result, or the output file path if output_filepath was given.

    Raises:
        ValueError: On invalid inputs.
        RuntimeError: On OSRM engine or service failure.
    """
    if not isinstance(coordinates, list):
        raise ValueError("coordinates must be a list of [lon, lat] pairs.")

    params = osrm.MatchParameters(
        coordinates=coordinates,
        timestamps=timestamps or [],
        gaps=gaps,
        tidy=tidy,
        steps=steps,
        number_of_alternatives=number_of_alternatives,
        annotations=annotations or [],
        geometries=geometries,
        overview=overview,
        continue_straight=continue_straight,
        waypoints=waypoints or [],
        hints=hints or [],
        radiuses=radiuses or [],
        bearings=bearings or [],
        approaches=approaches or [],
        generate_hints=generate_hints,
        exclude=exclude or [],
        snapping=snapping,
    )

    return _call_osrm(_build_engine(engine_config), "Match", params, output_filepath)


def osrm_trip(
    coordinates: list,
    source: str = "",
    destination: str = "",
    roundtrip: bool = True,
    steps: bool = False,
    number_of_alternatives: int = 0,
    annotations: list[str] | None = None,
    geometries: str = "",
    overview: str = "",
    continue_straight: bool | None = None,
    waypoints: list[int] | None = None,
    hints: list | None = None,
    radiuses: list | None = None,
    bearings: list | None = None,
    approaches: list | None = None,
    generate_hints: bool = True,
    exclude: list[str] | None = None,
    snapping: str = "",
    engine_config: dict | None = None,
    output_filepath: str | None = None,
) -> str:
    """Call the OSRM Trip service.

    Args:
        coordinates: List of [longitude, latitude] pairs.
        source: Start constraint — 'any' or 'first'.
        destination: End constraint — 'any' or 'last'.
        roundtrip: Return a roundtrip (route comes back to first coordinate).
        steps: Return turn-by-turn steps for each leg.
        number_of_alternatives: Number of alternative trips to search for.
        annotations: Per-step metadata.
        geometries: Route geometry format — 'polyline', 'polyline6', or 'geojson'.
        overview: Overview geometry detail — 'simplified', 'full', or 'false'.
        continue_straight: Force straight-ahead at waypoints.
        waypoints: Indices of coordinates treated as waypoints.
        hints: Hints from a previous request to speed up snapping.
        radiuses: Per-coordinate search radius in metres.
        bearings: Per-coordinate bearing constraints as (bearing, range) pairs.
        approaches: Per-coordinate curb-side constraint.
        generate_hints: Include snapping hints in the response.
        exclude: Road classes to avoid.
        snapping: 'default' or 'any'.
        engine_config: OSRM engine parameters. Defaults to DEFAULT_ENGINE_CONFIG when None.
        output_filepath: Write result JSON here and return the path; or return json.dumps str.

    Returns:
        JSON string of the result, or the output file path if output_filepath was given.

    Raises:
        ValueError: On invalid inputs.
        RuntimeError: On OSRM engine or service failure.
    """
    if not isinstance(coordinates, list):
        raise ValueError("coordinates must be a list of [lon, lat] pairs.")

    params = osrm.TripParameters(
        coordinates=coordinates,
        source=source,
        destination=destination,
        roundtrip=roundtrip,
        steps=steps,
        annotations=annotations or [],
        geometries=geometries,
        overview=overview,
        continue_straight=continue_straight,
        waypoints=waypoints or [],
        hints=hints or [],
        radiuses=radiuses or [],
        bearings=bearings or [],
        approaches=approaches or [],
        generate_hints=generate_hints,
        exclude=exclude or [],
        snapping=snapping,
    )

    return _call_osrm(_build_engine(engine_config), "Trip", params, output_filepath)


_SERVICE_FUNCTIONS = {
    "table": osrm_table,
    "route": osrm_route,
    "nearest": osrm_nearest,
    "match": osrm_match,
    "trip": osrm_trip,
}


def run_osrm_routing(
    input_coordinates: list,
    input_config: dict,
    osrm_service: str,
    engine_config: dict | None = None,
    output_filepath: str | None = None,
) -> str:
    """Call an OSRM service and return the result.

    Args:
        input_coordinates: List of [longitude, latitude] pairs.
        input_config: Service-specific parameters (e.g. sources/destinations for 'table').
            Keys must match the keyword arguments of the corresponding osrm_<service> function.
        osrm_service: One of 'table', 'route', 'nearest', 'match', 'trip'.
        engine_config: OSRM engine parameters. Defaults to DEFAULT_ENGINE_CONFIG when None.
        output_filepath: If provided, the result JSON is written to this path and the
            path is returned. If None (default), the result is returned as a json.dumps str.

    Returns:
        The result as a JSON string, or the output file path if output_filepath was given.

    Raises:
        ValueError: For invalid inputs (bad coordinates type, unknown service, etc.).
        RuntimeError: If the OSRM engine or service call fails.
    """
    if osrm_service not in _SERVICE_FUNCTIONS:
        raise ValueError(
            f"Unknown osrm_service {osrm_service!r}. "
            f"Must be one of: {list(_SERVICE_FUNCTIONS)}"
        )
    if not isinstance(input_coordinates, list):
        raise ValueError("input_coordinates must be a list of [lon, lat] pairs.")
    if not isinstance(input_config, dict):
        raise ValueError("input_config must be a dict of service-specific parameters.")

    return _SERVICE_FUNCTIONS[osrm_service](
        coordinates=input_coordinates,
        engine_config=engine_config,
        output_filepath=output_filepath,
        **input_config,
    )


def run(args: argparse.Namespace) -> None:

    engine_config = None

    # Load engine config from file
    if args.engine_config:
        engine_config = load_json_file(args.engine_config, "engine_config")

    # Load inputs
    coordinates = load_json_file(args.input_coordinates, "input_coordinates")
    service_params = load_json_file(args.input_config, "input_config")

    if not isinstance(coordinates, list):
        sys.exit("Error: input_coordinates must be a JSON array of [lon, lat] pairs.")
    if not isinstance(service_params, dict):
        sys.exit("Error: input_config must be a JSON object.")

    output_filepath = args.output_filepath

    try:
        result = run_osrm_routing(
            input_coordinates=coordinates,
            input_config=service_params,
            osrm_service=args.osrm_service,
            engine_config=engine_config,
            output_filepath=output_filepath,
        )
    except (ValueError, RuntimeError) as exc:
        sys.exit(f"Error: {exc}")

    if output_filepath:
        print(f"Result written to: {result}")
    else:
        print(result)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    run(args)


def test_table_service() -> str:

    current_os = platform.system()
    is_windows = False
    if current_os == "Windows":
        is_windows = True

    results = osrm_table(
        coordinates=[
            [-77.4688, 39.6225],  # Cunningham Falls State Park, Catoctin Mountains
            [-75.4408, 38.1294],  # Pocomoke River State Park, Lower Eastern Shore
            [-75.1372, 38.2375],  # Assateague State Park, Atlantic Coast
            [-77.2492, 39.1509],  # Seneca Creek State Park, Montgomery County
        ],
        sources=[0, 1],
        destinations=[1, 2],
        # duration is in seconds and distance is in meters
        annotations=["duration", "distance"],
        engine_config={'storage_config': f'data/{'windows' if is_windows else 'linux'}/maryland-260621.osrm', 'use_shared_memory': False, 'use_mmap': True}
    )
    return results

if __name__ == "__main__":
    print("main")
