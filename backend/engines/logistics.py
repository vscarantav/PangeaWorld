"""Landed-cost calculations shared by resource trades and market previews."""

MODE_MULTIPLIERS = {
    "sea": 2.0,
    "river": 5.0,
    "rail": 12.0,
    "air": 30.0,
}
DISTANCE_PER_EDGE_KM = 100


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
