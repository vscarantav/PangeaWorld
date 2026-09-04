"""Resource production, scarcity, and trade operations."""

from .logistics import calculate_landed_cost


def produce_resources(nation, round_number: int = 1, consumption: dict[str, float] | None = None) -> list[dict]:
    """Apply one round of production, depletion, and optional consumption."""
    if round_number < 1:
        raise ValueError("round_number must be positive")
    consumption = consumption or {}
    results = []
    for resource in nation.resources:
        name = getattr(resource.type, "value", resource.type)
        before = float(resource.stockpile or 0.0)
        produced = max(0.0, float(resource.production_rate or 0.0))
        depleted = min(produced, max(0.0, float(resource.depletion_rate or 0.0)))
        consumed = min(before + produced - depleted, max(0.0, float(consumption.get(name, 0.0))))
        resource.stockpile = round(max(0.0, before + produced - depleted - consumed), 4)
        results.append({
            "type": name, "before": before, "produced": produced,
            "depleted": depleted, "consumed": consumed,
            "after": resource.stockpile,
        })
    return results


def calculate_scarcity(resource_type: str, resources, demand: float) -> dict[str, float | str]:
    """Return supply, demand, and a bounded scarcity price multiplier."""
    target = getattr(resource_type, "value", resource_type)
    supply = sum(
        max(0.0, float(r.stockpile or 0.0))
        for r in resources
        if getattr(r.type, "value", r.type) == target
    )
    demand = max(0.0, float(demand))
    if supply == 0 and demand == 0:
        multiplier = 1.0
    elif supply == 0:
        multiplier = 3.0
    else:
        multiplier = min(3.0, max(0.5, demand / supply))
    return {"resource_type": target, "supply": round(supply, 4), "demand": round(demand, 4), "price_multiplier": round(multiplier, 4)}


def process_trade(exporter_resource, importer_resource, quantity: float, route: dict) -> dict:
    """Transfer stock between resource records and return the cost breakdown."""
    quantity = float(quantity)
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    if exporter_resource.type != importer_resource.type:
        raise ValueError("exporter and importer resources must have the same type")
    if exporter_resource.stockpile < quantity:
        raise ValueError("exporter does not have enough stockpile")
    cost = calculate_landed_cost(**route)
    exporter_resource.stockpile = round(exporter_resource.stockpile - quantity, 4)
    importer_resource.stockpile = round(importer_resource.stockpile + quantity, 4)
    total_cost = round(float(cost["unit_cost"]) * quantity, 4)
    return {"quantity": quantity, "total_cost": total_cost, "unit_cost": cost["unit_cost"], "cost_breakdown": cost}
