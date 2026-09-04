"""Validation and persistence helpers for session-locked map snapshots."""


def normalize_map_snapshot(snapshot: dict) -> dict:
    """Validate the client-provided canonical map summary and return a copy."""
    if not isinstance(snapshot, dict):
        raise ValueError("map_snapshot must be an object")
    required = {"seed", "triangles", "edges", "countries"}
    missing = required.difference(snapshot)
    if missing:
        raise ValueError(f"map_snapshot is missing: {', '.join(sorted(missing))}")
    if not isinstance(snapshot["seed"], str) or not snapshot["seed"]:
        raise ValueError("map_snapshot.seed must be a non-empty string")
    for key in ("triangles", "edges", "countries"):
        if not isinstance(snapshot[key], list) or not snapshot[key]:
            raise ValueError(f"map_snapshot.{key} must be a non-empty list")
    if len(snapshot["countries"]) != 8:
        raise ValueError("map_snapshot must contain exactly 8 countries")
    triangle_ids = {triangle.get("id") for triangle in snapshot["triangles"]}
    if None in triangle_ids:
        raise ValueError("every map triangle must have an id")
    for edge in snapshot["edges"]:
        if edge.get("is_impassable"):
            continue
        if any(triangle_id not in triangle_ids for triangle_id in edge.get("triangle_ids", [])):
            raise ValueError("map edge references an unknown triangle")
        if any(triangle.get("id") in edge.get("triangle_ids", []) and triangle.get("terrain") == "Ocean"
               for triangle in snapshot["triangles"]):
            raise ValueError("passable map edges cannot touch ocean")
    return snapshot
