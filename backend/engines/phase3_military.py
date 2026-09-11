"""Deterministic direct-conflict rules for the Phase 3 Sprint 2 vertical slice.

The resolver deliberately has no database dependency.  Its sole inputs are
persisted round state, so the same order always produces the same public
outcome after a reconnect or a processing retry.
"""

from __future__ import annotations

import hashlib
import math
from typing import Any


UNIT_COSTS = {"infantry": 100.0, "navy": 250.0, "air_force": 350.0}
UNIT_ATTACK = {"infantry": 1, "navy": 2, "air_force": 3}
UNIT_DEFENSE = {"infantry": 1, "navy": 2, "air_force": 1}
UNIT_TYPES = tuple(UNIT_COSTS)


def normalized_units(units: dict | None) -> dict[str, int]:
    """Return the canonical inventory shape and reject untrusted unit maps."""
    source = {} if units is None else units
    if not isinstance(source, dict):
        raise ValueError("military units must be an object")
    normalized = {}
    for unit_type in UNIT_TYPES:
        value = source.get(unit_type, 0)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{unit_type} must be a non-negative whole number")
        normalized[unit_type] = value
    if any(key not in UNIT_TYPES for key in source):
        raise ValueError("unsupported military unit type")
    return normalized


def procurement_cost(units: dict | None) -> float:
    order = normalized_units(units)
    return round(sum(UNIT_COSTS[unit_type] * count for unit_type, count in order.items()), 2)


def validate_attack_order(*, attacker_nation_id: int, target_nation_id: int,
                          units: dict | None, inventory: dict | None) -> dict[str, int]:
    if attacker_nation_id == target_nation_id:
        raise ValueError("a nation cannot target itself")
    deployment = normalized_units(units)
    if not sum(deployment.values()):
        raise ValueError("an attack must deploy at least one unit")
    available = normalized_units(inventory)
    for unit_type, count in deployment.items():
        if count > available[unit_type]:
            raise ValueError(f"cannot deploy more {unit_type} than the national inventory")
    return deployment


def _rolls(seed: str, count: int) -> list[int]:
    return [int(hashlib.sha256(f"{seed}:{index}".encode()).hexdigest()[:8], 16) % 6 + 1 for index in range(count)]


def _remove_casualties(inventory: dict[str, int], casualties: int) -> dict[str, int]:
    """Lose strongest units first: a visible, deterministic conservative rule."""
    remaining = dict(inventory)
    for unit_type in sorted(UNIT_TYPES, key=lambda item: (UNIT_ATTACK[item] + UNIT_DEFENSE[item], item), reverse=True):
        lost = min(remaining[unit_type], casualties)
        remaining[unit_type] -= lost
        casualties -= lost
        if not casualties:
            break
    return remaining


def resolve_attack(*, session_seed: str, round_number: int, attacker_id: int,
                   target_id: int, deployment: dict | None, attacker_inventory: dict | None,
                   defender_inventory: dict | None, attacker_atk: int, defender_def: int,
                   attacker_readiness: float = 0.0, defender_readiness: float = 0.0,
                   defender_posture: str = "defend") -> dict[str, Any]:
    """Resolve one bounded attack using seeded dice and persisted force levels."""
    deployed = validate_attack_order(attacker_nation_id=attacker_id, target_nation_id=target_id,
                                     units=deployment, inventory=attacker_inventory)
    attacker_force = normalized_units(attacker_inventory)
    defender_force = normalized_units(defender_inventory)
    posture_bonus = {"defend": 2, "patrol": 1, "reconnaissance": 0}.get(defender_posture, 0)
    attack_index = min(10, max(1, int(attacker_atk) + math.floor(float(attacker_readiness) / 100) + sum(UNIT_ATTACK[k] * v for k, v in deployed.items()) // 3))
    defense_index = min(10, max(1, int(defender_def) + posture_bonus + math.floor(float(defender_readiness) / 100) + sum(UNIT_DEFENSE[k] * v for k, v in defender_force.items()) // 8))
    attack_dice = min(5, max(1, math.ceil(attack_index / 2)))
    defense_dice = min(5, max(1, math.ceil(defense_index / 2)))
    key = f"phase3-attack:{session_seed}:{round_number}:{attacker_id}:{target_id}:{','.join(f'{k}={deployed[k]}' for k in UNIT_TYPES)}"
    attacker_rolls = _rolls(f"{key}:attacker", attack_dice)
    defender_rolls = _rolls(f"{key}:defender", defense_dice)
    attacker_score, defender_score = sum(attacker_rolls), sum(defender_rolls)
    attacker_won = attacker_score > defender_score or (attacker_score == defender_score and attack_index > defense_index)

    attacker_deployed_total = sum(deployed.values())
    attacker_losses = max(1, math.ceil(attacker_deployed_total * (0.20 if attacker_won else 0.45)))
    defender_total = sum(defender_force.values())
    defender_losses = min(defender_total, max(1, math.ceil(defender_total * (0.30 if attacker_won else 0.10)))) if defender_total else 0
    # Only deployed attacking units can be lost.  Survivors return home.
    surviving_deployment = _remove_casualties(deployed, min(attacker_deployed_total, attacker_losses))
    post_attack_attacker = dict(attacker_force)
    for unit_type in UNIT_TYPES:
        post_attack_attacker[unit_type] -= deployed[unit_type] - surviving_deployment[unit_type]
    post_attack_defender = _remove_casualties(defender_force, defender_losses)
    return {
        "attacker_id": attacker_id, "target_id": target_id, "outcome": "attacker_victory" if attacker_won else "defender_holds",
        "attack_index": attack_index, "defense_index": defense_index,
        "attacker_rolls": attacker_rolls, "defender_rolls": defender_rolls,
        "attacker_score": attacker_score, "defender_score": defender_score,
        "deployment": deployed, "attacker_losses": min(attacker_deployed_total, attacker_losses),
        "defender_losses": defender_losses, "attacker_inventory_after": post_attack_attacker,
        "defender_inventory_after": post_attack_defender, "reproducibility_key": key,
    }


def public_attack_article(*, effect_id: int, round_number: int, attacker_name: str,
                          target_name: str, outcome: str, attacker_losses: int, defender_losses: int,
                          control_transferred: int = 0) -> dict[str, Any]:
    if outcome == "attacker_retreats":
        return {"id": f"phase3-combat-{effect_id}", "round": round_number, "category": "Security", "impact": "High",
                "headline": f"{attacker_name} retreats from clash with {target_name}",
                "summary": f"Public losses: attacker {attacker_losses}; defender {defender_losses}."}
    if outcome == "attack_cancelled":
        return {
            "id": f"phase3-combat-{effect_id}", "round": round_number, "category": "Security",
            "impact": "High", "headline": f"{attacker_name}'s attack on {target_name} is cancelled",
            "summary": "Earlier combat losses left no committed units available. No additional losses occurred.",
        }
    headline = (f"{attacker_name} claims a tactical victory in clash with {target_name}"
                if outcome == "attacker_victory"
                else f"{attacker_name} is repelled in clash with {target_name}")
    control_summary = (f" {attacker_name} gained one strategic control point; national borders remain unchanged."
                       if control_transferred else " No strategic control changed hands.")
    return {
        "id": f"phase3-combat-{effect_id}", "round": round_number, "category": "Security",
        "impact": "High", "headline": headline,
        "summary": f"Public military losses: {attacker_name} {attacker_losses}; {target_name} {defender_losses}.{control_summary}",
    }


def resolve_battle(*, engagement_limit=1, retreat_threshold=0.5, **inputs):
    """Resolve up to three engagements; retreat is a precommitted loss limit."""
    starting = normalized_units(inputs["deployment"])
    original_total = sum(starting.values())
    force = dict(starting)
    attacker_inventory = normalized_units(inputs["attacker_inventory"])
    defender_inventory = normalized_units(inputs["defender_inventory"])
    attacker_losses = defender_losses = 0
    for engagement in range(engagement_limit):
        result = resolve_attack(**{**inputs, "session_seed": inputs["session_seed"] if engagement == 0 else f"{inputs['session_seed']}:engagement:{engagement}",
            "deployment": force, "attacker_inventory": attacker_inventory, "defender_inventory": defender_inventory})
        for kind in force:
            force[kind] -= attacker_inventory[kind] - result["attacker_inventory_after"][kind]
        attacker_inventory = result["attacker_inventory_after"]
        defender_inventory = result["defender_inventory_after"]
        attacker_losses += result["attacker_losses"]
        defender_losses += result["defender_losses"]
        if result["outcome"] == "attacker_victory" or not any(force.values()):
            break
        if attacker_losses / original_total >= retreat_threshold:
            result["outcome"] = "attacker_retreats"
            break
    return {**result, "attacker_losses": attacker_losses, "defender_losses": defender_losses,
            "engagements": engagement + 1, "attacker_inventory_after": attacker_inventory,
            "defender_inventory_after": defender_inventory}


def operation_cost(operation):
    if not operation:
        return 0.0
    return {"attack": 0.0, "blockade": 50.0, "intelligence": 25.0}.get(operation["operation_type"], 0.0)


def apply_strategic_control(attacker, defender, outcome):
    """Transfer one abstract strategic zone without rewriting national map geometry."""
    attacker_policies = dict(attacker.policies or {})
    defender_policies = dict(defender.policies or {})
    attacker_before = max(1, int(attacker_policies.get("strategic_control_points", 3)))
    defender_before = max(1, int(defender_policies.get("strategic_control_points", 3)))
    transferred = int(outcome == "attacker_victory" and defender_before > 1)
    attacker_after = attacker_before + transferred
    defender_after = defender_before - transferred
    attacker.policies = {**attacker_policies, "strategic_control_points": attacker_after}
    defender.policies = {**defender_policies, "strategic_control_points": defender_after}
    return {
        "control_transferred": transferred,
        "attacker_control_before": attacker_before,
        "attacker_control_after": attacker_after,
        "defender_control_before": defender_before,
        "defender_control_after": defender_after,
        "control_model": "abstract_strategic_zones",
    }
