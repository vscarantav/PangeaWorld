"""Auditable, deterministic vacant-seat behavior; no model chooses game outcomes."""
from .phase3_military import normalized_units


def drakmoor_order(session, nation):
    mode = (session.phase3_settings or {}).get("drakmoor_mode", "scripted")
    if mode == "passive":
        return {}
    inventory = normalized_units(nation.military_inventory)
    if not any(inventory.values()):
        return {}
    targets = sorted((item for item in session.nations if item.id != nation.id), key=lambda item: (item.military_def, item.id))
    if not targets:
        return {}
    kind = "intelligence" if session.current_round == 1 else "attack"
    if kind == "intelligence" and nation.treasury < 25:
        return {}
    # Risk no more than half the force; keep the rest available for defense.
    deployed = {key: max(1, value // 2) if value else 0 for key, value in inventory.items()}
    return {"military_operation": {"operation_type": kind, "target_nation_id": targets[0].id,
        "units": deployed, "engagement_limit": 2, "retreat_threshold": 0.5}}
