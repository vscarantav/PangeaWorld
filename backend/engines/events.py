"""Seeded world events. The same session seed and round always produce the same events."""

import hashlib

EVENT_TEMPLATES = [
    {"category": "natural_disaster", "headline": "Severe storms disrupt regional energy output", "impact": "High", "production_multiplier": 0.75, "resource_type": "Energy", "approval_delta": -3.0, "damages_infrastructure": True},
    {"category": "political_crisis", "headline": "A labor strike slows industrial activity", "impact": "Medium", "production_multiplier": 0.85, "resource_type": "Labor", "approval_delta": -4.0},
    {"category": "market_shock", "headline": "Commodity markets react to a sudden supply squeeze", "impact": "Medium", "cpi_delta": 3.0, "approval_delta": -2.0},
    {"category": "health_emergency", "headline": "A regional health emergency reduces available workers", "impact": "High", "production_multiplier": 0.8, "resource_type": "Labor", "approval_delta": -3.0},
    {"category": "technology_breakthrough", "headline": "A new production technique boosts technology output", "impact": "Low", "production_multiplier": 1.2, "resource_type": "Technology", "approval_delta": 2.0},
]


def _number(seed: str, round_number: int, salt: int) -> int:
    digest = hashlib.sha256(f"{seed}:{round_number}:{salt}".encode()).hexdigest()
    return int(digest[:12], 16)


EVENT_RULESET = "phase3-events-v2"


def event_schedule(seed: str) -> list[dict]:
    """Fourteen seeded events: three major and eleven minor over seven years.

    Slot IDs are stable independently of ORM relationship ordering. Instructor
    injections and reactive incidents are additional, explicitly marked events.
    """
    major_slots = set(sorted(range(14), key=lambda slot: (_number(seed, slot, 700), slot))[:3])
    return [{"round": slot // 2 + 1, "slot": slot, "scale": "major" if slot in major_slots else "minor"}
            for slot in range(14)]


def generate_round_events(session, round_) -> list[dict]:
    if getattr(session, "ruleset_version", "legacy-v1") != "phase3-closure-v1":
        return _legacy_round_events(session, round_)
    nations = sorted(session.nations, key=lambda nation: nation.id)
    if not nations:
        return []
    events = []
    for slot in event_schedule(session.seed):
        if slot["round"] != round_.number:
            continue
        index = slot["slot"]
        template = EVENT_TEMPLATES[_number(session.seed, round_.number, index + 1) % len(EVENT_TEMPLATES)]
        target = nations[_number(session.seed, round_.number, index + 10) % len(nations)]
        event = dict(template)
        # Major incidents amplify the effect, without changing terrain rules.
        factor = 2 if slot["scale"] == "major" else 1
        for key in ("cpi_delta", "approval_delta"):
            if key in event:
                event[key] *= factor
        if "production_multiplier" in event:
            event["production_multiplier"] = max(0.25, 1 + (event["production_multiplier"] - 1) * factor)
        event.update({"id": f"r{round_.number}-e{index + 1}", "round": round_.number,
                      "nation_id": target.id, "scale": slot["scale"], "source": "scheduled",
                      "ruleset_version": EVENT_RULESET, "impact": "High" if factor == 2 else "Medium"})
        events.append(event)
    previous = next((item for item in getattr(session, "rounds", []) if item.number == round_.number - 1), None)
    previous_unrest = {event.get("nation_id") for event in (previous.events or [])
                       if event.get("trigger") == "cpi_above_115"} if previous else set()
    for nation in nations:
        if float(getattr(nation, "cpi", 100) or 100) > 115 and nation.id not in previous_unrest:
            events.append({"id": f"r{round_.number}-unrest-{nation.id}", "round": round_.number,
                "nation_id": nation.id, "category": "political_crisis", "source": "reactive",
                "trigger": "cpi_above_115", "observed_cpi": float(nation.cpi), "impact": "Medium",
                "headline": "High consumer prices trigger civil unrest", "approval_delta": -3.0,
                "resource_type": "Labor", "production_multiplier": 0.9, "ruleset_version": EVENT_RULESET})
    return events


def event_effects(events: list[dict], nation_id: int) -> dict:
    """Return temporary production, price, and approval effects for a nation."""
    multipliers = {}
    cpi_delta = 0.0
    approval_delta = 0.0
    for event in events:
        if event.get("nation_id") != nation_id:
            continue
        resource_type = event.get("resource_type")
        if resource_type and "production_multiplier" in event:
            multipliers[resource_type] = multipliers.get(resource_type, 1.0) * float(event["production_multiplier"])
        cpi_delta += float(event.get("cpi_delta", 0.0))
        approval_delta += float(event.get("approval_delta", 0.0))
    return {"production_multipliers": multipliers, "cpi_delta": cpi_delta, "approval_delta": approval_delta}

def _legacy_round_events(session, round_) -> list[dict]:
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
