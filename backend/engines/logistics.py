"""Landed-cost calculations shared by resource trades and market previews."""

import math

MODE_MULTIPLIERS = {
    "sea": 2.0,
    "river": 5.0,
    "rail": 12.0,
    "air": 30.0,
}
DISTANCE_PER_EDGE_KM = 100
MAP_EDGE_LENGTH = 7
MODE_TRANSIT_ROUNDS = {"sea": 3, "river": 2, "rail": 1, "air": 0}


def calculate_landed_cost(
    base_price: float,
    distance_edges: int,
    mode: str = "rail",
    freight: float = 1.0,
    tariff_rate: float = 0.0,
    insurance_rate: float = 0.0,
    port_fees: float = 0.0,
) -> dict[str, float | str]:
    """Calculate per-unit landed cost from the canonical route formula."""
    normalized_mode = mode.lower()
    if normalized_mode not in MODE_MULTIPLIERS:
        raise ValueError(f"Unsupported transport mode: {mode}")
    if distance_edges < 0:
        raise ValueError("distance_edges cannot be negative")
    base = float(base_price)
    freight_cost = float(freight) * distance_edges * MODE_MULTIPLIERS[normalized_mode]
    tariff = (base + freight_cost) * float(tariff_rate)
    insurance = (base + freight_cost) * float(insurance_rate)
    total = base + freight_cost + tariff + insurance + float(port_fees)
    return {
        "mode": normalized_mode,
        "distance_km": float(distance_edges * DISTANCE_PER_EDGE_KM),
        "base_price": round(base, 4),
        "freight": round(freight_cost, 4),
        "tariffs": round(tariff, 4),
        "insurance": round(insurance, 4),
        "port_fees": round(float(port_fees), 4),
        "unit_cost": round(total, 4),
    }


def estimate_route(map_snapshot: dict | None, origin_name: str, destination_name: str, mode: str) -> dict:
    """Estimate a route from the immutable map snapshot's country anchors.

    Phase 1 stores the full triangle graph, but it does not yet store dedicated
    sea-lane/airway route records. Country-anchor distance keeps previews and
    round processing deterministic while still making geography authoritative.
    """
    normalized_mode = mode.lower()
    if normalized_mode not in MODE_MULTIPLIERS:
        raise ValueError(f"Unsupported transport mode: {mode}")
    countries = (map_snapshot or {}).get("countries") or []
    by_name = {str(country.get("name", "")).lower(): country for country in countries}
    origin = by_name.get(origin_name.lower())
    destination = by_name.get(destination_name.lower())
    if origin_name == destination_name:
        distance_edges = 1
    elif origin and destination and all(key in origin and key in destination for key in ("x", "y")):
        pixels = math.hypot(float(origin["x"]) - float(destination["x"]), float(origin["y"]) - float(destination["y"]))
        distance_edges = max(1, math.ceil(pixels / MAP_EDGE_LENGTH))
    else:
        # Older snapshots lacked anchor coordinates. Keep those sessions
        # playable with a conservative deterministic fallback.
        distance_edges = 10

    if normalized_mode == "sea" and origin_name != destination_name:
        port_country_ids = {
            str(city.get("country_id"))
            for city in (map_snapshot or {}).get("cities", [])
            if city.get("is_port")
        }
        if not origin or not destination or str(origin.get("id")) not in port_country_ids or str(destination.get("id")) not in port_country_ids:
            raise ValueError("sea freight requires a port in both nations")

    return {
        "distance_edges": distance_edges,
        "distance_km": distance_edges * DISTANCE_PER_EDGE_KM,
        "mode": normalized_mode,
        "transit_rounds": MODE_TRANSIT_ROUNDS[normalized_mode],
    }
