"""Validation and persistence helpers for session-locked map snapshots."""

import re


def normalize_map_snapshot(snapshot: dict) -> dict:
    """Validate the client-provided canonical map summary and return a copy."""
    if not isinstance(snapshot, dict):
        raise ValueError("map_snapshot must be an object")
    required = {"seed", "triangles", "edges", "countries", "cities"}
    missing = required.difference(snapshot)
    if missing:
        raise ValueError(f"map_snapshot is missing: {', '.join(sorted(missing))}")
    if not isinstance(snapshot["seed"], str) or not snapshot["seed"]:
        raise ValueError("map_snapshot.seed must be a non-empty string")
    for key in ("triangles", "edges", "countries"):
        if not isinstance(snapshot[key], list) or not snapshot[key]:
            raise ValueError(f"map_snapshot.{key} must be a non-empty list")
        if not all(isinstance(item, dict) for item in snapshot[key]):
            raise ValueError(f"map_snapshot.{key} entries must be objects")
    if len(snapshot["countries"]) != 8:
        raise ValueError("map_snapshot must contain exactly 8 countries")
    if not all(isinstance(item, dict) for item in snapshot["cities"]):
        raise ValueError("map_snapshot.cities entries must be objects")
    if not all(isinstance(item.get("id"), (str, int)) for item in snapshot["triangles"]):
        raise ValueError("every map triangle must have an id")
    triangle_ids = {triangle["id"] for triangle in snapshot["triangles"]}
    if len(triangle_ids) != len(snapshot["triangles"]):
        raise ValueError("map triangle ids must be unique")
    compact_geometry = snapshot.get("version", 0) >= 3
    for triangle in snapshot["triangles"]:
        points = triangle.get("points", [])
        has_stored_geometry = (
            isinstance(points, list)
            and len(points) == 3
            and all(
                isinstance(point, dict)
                and isinstance(point.get("x"), (int, float))
                and isinstance(point.get("y"), (int, float))
                for point in points
            )
        )
        has_compact_geometry = compact_geometry and re.fullmatch(r"\d+-\d+", str(triangle["id"]))
        if not has_stored_geometry and not has_compact_geometry:
            raise ValueError("every map triangle must contain valid geometry")
    if not all(isinstance(item.get("id"), (str, int)) and isinstance(item.get("name"), str) for item in snapshot["countries"]):
        raise ValueError("every map country must have a string name and id")
    country_ids = {country["id"] for country in snapshot["countries"]}
    country_names = {country["name"] for country in snapshot["countries"]}
    expected_names = {"Terranova", "Solhaven", "Korvath", "Valdoria", "Nordvik", "Zephyria", "Drakmoor", "Lunara"}
    if len(country_ids) != 8 or country_names != expected_names:
        raise ValueError("map must contain the eight canonical countries with unique ids")
    if not all(isinstance(item.get("id"), (str, int)) for item in snapshot["cities"]):
        raise ValueError("map city ids must be unique and present")
    city_ids = {city["id"] for city in snapshot["cities"]}
    if len(city_ids) != len(snapshot["cities"]):
        raise ValueError("map city ids must be unique and present")
    if len(snapshot["cities"]) != 64:
        raise ValueError("map must contain exactly 8 cities per country")
    city_counts = {country_id: 0 for country_id in country_ids}
    port_counts = {country_id: 0 for country_id in country_ids}
    for city in snapshot["cities"]:
        if city.get("triangle_id") not in triangle_ids or city.get("country_id") not in country_ids:
            raise ValueError("map city references an unknown triangle or country")
        city_counts[city["country_id"]] += 1
        if city.get("is_port"):
            port_counts[city["country_id"]] += 1
    if any(count != 8 for count in city_counts.values()):
        raise ValueError("map must contain exactly 8 cities per country")
    country_by_name = {country["name"]: country["id"] for country in snapshot["countries"]}
    expected_ports = {name: (2 if name in {"Nordvik", "Lunara"} else 1 if name == "Drakmoor" else 0) for name in expected_names}
    for name, expected in expected_ports.items():
        if port_counts[country_by_name[name]] != expected:
            raise ValueError(f"{name} must have exactly {expected} starting ports")
    if not all(isinstance(item.get("id"), (str, int)) for item in snapshot["edges"]):
        raise ValueError("map edge ids must be unique and present")
    edge_ids = {edge["id"] for edge in snapshot["edges"]}
    if len(edge_ids) != len(snapshot["edges"]):
        raise ValueError("map edge ids must be unique and present")
    terrain_by_triangle_id = {triangle["id"]: triangle.get("terrain") for triangle in snapshot["triangles"]}
    mountain_ids = {triangle_id for triangle_id, terrain in terrain_by_triangle_id.items() if terrain in {"Impassable Peaks", "Mountain"}}
    passable_mountain_edges = {triangle_id: 0 for triangle_id in mountain_ids}
    for edge in snapshot["edges"]:
        triangle_ids_for_edge = edge.get("triangle_ids", [])
        if not isinstance(triangle_ids_for_edge, list) or not triangle_ids_for_edge:
            raise ValueError("every map edge must reference at least one triangle")
        if any(triangle_id not in triangle_ids for triangle_id in triangle_ids_for_edge):
            raise ValueError("map edge references an unknown triangle")
        if any(terrain_by_triangle_id[triangle_id] == "Ocean" for triangle_id in triangle_ids_for_edge):
            if not edge.get("is_impassable"):
                raise ValueError("passable map edges cannot touch ocean")
        if not edge.get("is_impassable"):
            for triangle_id in triangle_ids_for_edge:
                if triangle_id in passable_mountain_edges:
                    passable_mountain_edges[triangle_id] += 1
    if any(count != 1 for count in passable_mountain_edges.values()):
        raise ValueError("every mountain triangle must have exactly one passable edge")
    return snapshot
