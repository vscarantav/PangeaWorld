"""Seeded world events. The same session seed and round always produce the same events."""

import hashlib

EVENT_TEMPLATES = [
    {"category": "natural_disaster", "headline": "Severe storms disrupt regional energy output", "impact": "High", "production_multiplier": 0.75, "resource_type": "Energy"},
    {"category": "political_crisis", "headline": "A labor strike slows industrial activity", "impact": "Medium", "production_multiplier": 0.85, "resource_type": "Labor"},
    {"category": "market_shock", "headline": "Commodity markets react to a sudden supply squeeze", "impact": "Medium", "cpi_delta": 3.0},
    {"category": "health_emergency", "headline": "A regional health emergency reduces available workers", "impact": "High", "production_multiplier": 0.8, "resource_type": "Labor"},
    {"category": "technology_breakthrough", "headline": "A new production technique boosts technology output", "impact": "Low", "production_multiplier": 1.2, "resource_type": "Technology"},
]


def _number(seed: str, round_number: int, salt: int) -> int:
    digest = hashlib.sha256(f"{seed}:{round_number}:{salt}".encode()).hexdigest()
    return int(digest[:12], 16)


def generate_round_events(session, round_) -> list[dict]:
    """Generate one or two stable events and assign each to a nation."""
    nations = list(session.nations)
    if not nations:
        return []
    count = 1 + (_number(session.seed, round_.number, 0) % 2)
    events = []
    for index in range(count):
        template = EVENT_TEMPLATES[_number(session.seed, round_.number, index + 1) % len(EVENT_TEMPLATES)]
        target = nations[_number(session.seed, round_.number, index + 10) % len(nations)]
        event = dict(template)
        event.update({"id": f"r{round_.number}-e{index + 1}", "round": round_.number, "nation_id": target.id})
        events.append(event)
    return events


def event_effects(events: list[dict], nation_id: int) -> tuple[dict[str, float], float]:
    """Return temporary production multipliers and CPI delta for one nation."""
    multipliers = {}
    cpi_delta = 0.0
    for event in events:
        if event.get("nation_id") != nation_id:
            continue
        resource_type = event.get("resource_type")
        if resource_type and "production_multiplier" in event:
            multipliers[resource_type] = multipliers.get(resource_type, 1.0) * float(event["production_multiplier"])
        cpi_delta += float(event.get("cpi_delta", 0.0))
    return multipliers, cpi_delta
