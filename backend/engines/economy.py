"""Small, deterministic macroeconomic calculations for a single round."""

from collections.abc import Iterable

RESOURCE_WEIGHTS = {
    "Energy": 0.25,
    "Minerals": 0.15,
    "Agriculture": 0.20,
    "Technology": 0.15,
    "Labor": 0.15,
    "Capital": 0.10,
}


def calculate_gdp(nation, government_spending: float = 0.0, net_exports: float | None = None) -> float:
    """Return GDP as company revenue plus government spending and net exports."""
    company_revenue = sum(float(company.revenue or 0.0) for company in nation.companies)
    exports = float(nation.trade_balance if net_exports is None else net_exports)
    return max(0.0, company_revenue + float(government_spending) + exports)


def calculate_cpi(nation, resource_demands: dict[str, float] | None = None) -> float:
    """Estimate CPI from weighted demand relative to normal production.

    Stockpiles are buffers, not an unlimited source of price deflation. When no
    demand is supplied, each resource is at its baseline demand and CPI is
    therefore stable. Explicitly higher demand can move CPI upward, while the
    bounded multiplier prevents a single resource from destroying the index.
    """
    demands = resource_demands or {}
    pressure = 0.0
    for resource in nation.resources:
        resource_name = getattr(resource.type, "value", resource.type)
        production = float(resource.production_rate or 0.0)
        demand = float(demands.get(resource_name, production))
        if production <= 0 and demand <= 0:
            continue
        supply = max(0.01, production)
        multiplier = min(1.5, max(0.75, demand / supply))
        pressure += RESOURCE_WEIGHTS.get(resource_name, 0.0) * multiplier
    covered_weight = sum(
        weight for name, weight in RESOURCE_WEIGHTS.items()
        if any(
            getattr(r.type, "value", r.type) == name
            and (float(r.production_rate or 0.0) > 0 or float(demands.get(name, 0.0)) > 0)
            for r in nation.resources
        )
    )
    if covered_weight == 0:
        return float(nation.cpi or 100.0)
    normalized_pressure = pressure / covered_weight
    return round(float(nation.cpi or 100.0) * normalized_pressure, 4)


def calculate_inflation(current_cpi: float, previous_cpi: float) -> float:
    """Return percentage CPI change; zero is returned for a zero baseline."""
    if previous_cpi == 0:
        return 0.0
    return round((float(current_cpi) / float(previous_cpi) - 1.0) * 100.0, 4)


def calculate_unemployment(company_headcount: int, labor_pool: int) -> float:
    """Return unemployed labor as a percentage of the labor pool."""
    if labor_pool <= 0:
        return 0.0
    employed = min(max(int(company_headcount), 0), int(labor_pool))
    return round((1.0 - employed / labor_pool) * 100.0, 4)


def calculate_trade_balance(exports: Iterable[float], imports: Iterable[float]) -> float:
    """Return total export value minus total import value."""
    return round(sum(float(value) for value in exports) - sum(float(value) for value in imports), 4)
