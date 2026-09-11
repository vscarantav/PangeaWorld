"""Versioned, server-quoted feasible allocations and immutable reasoning records."""
from copy import deepcopy
import hashlib
import json
import math

RULESET = "phase3-closure-v1"


def build_review(player_type, decision, available, committed, quote, normalize, context, project):
    selected = deepcopy(decision)
    selected.pop("opportunity_cost", None)
    candidates = []
    if player_type == "president":
        base = {**selected, "government_spending": 0.0, "military_investment": 0.0,
                "emergency_preparedness_investment": 0.0, "military_procurement": {}, "military_operation": None}
        amount = min(available, max(100.0, committed))
        variants = [("reserve", "Keep funds and units available", base),
            ("civilian", "Fund civilian services", {**base, "government_spending": amount}),
            ("preparedness", "Fund disaster recovery", {**base, "emergency_preparedness_investment": amount})]
        marginal = "Each additional $100M of readiness consumes $100M available for services or recovery; military strength has diminishing returns and a cap. Procurement arrives after operations."
    else:
        base = {**selected, "rnd_investment": 0.0, "headcount": 0, "production_units": 0.0, "sourcing": []}
        variants = [("reserve", "Pause production and retain cash", base),
            ("research", "Invest in future quality", {**base, "rnd_investment": min(100.0, available)}),
            ("production", "Maintain baseline production", {**base, "production_units": 1.0})]
        marginal = "Additional production reserves 10% of baseline COGS as working capital and uses limited capacity; sales finance the remaining operating costs. Hiring has a recurring wage cost. Additional R&D improves future quality with diminishing returns."
    for candidate_id, label, allocation in variants:
        allocation = normalize(allocation)
        if allocation == selected or any(item["allocation"] == allocation for item in candidates):
            continue
        try:
            cost = quote(allocation)
        except ValueError:
            continue
        if cost > available:
            continue
        candidates.append({"id": candidate_id, "label": label, "allocation": allocation,
                           "commitment": round(cost, 4), "remaining": round(available - cost, 4), "projection": project(allocation, cost)})
    assumptions = {"available": available, "committed": round(committed, 4),
        "remaining": round(available - committed, 4), "ruleset_version": RULESET,
        "resource": "treasury and existing units" if player_type == "president" else "cash, labor and production capacity",
        "recurring_cost": 0.0 if player_type == "president" else round(selected.get("headcount", 0) * 0.05, 4),
        "marginal_tradeoff": marginal,
        "uncertainty": "Forecasts hold current rules and available resources fixed; events, opposing orders and supplier competition can change outcomes."}
    content = {"context": context, "selected": selected, "selected_projection": project(selected, committed), "alternatives": candidates, "assumptions": assumptions}
    token = hashlib.sha256(json.dumps(content, sort_keys=True, default=str).encode()).hexdigest()
    return {**content, "preview_token": token}


def validate_reasoning(evidence, review):
    if not isinstance(evidence, dict):
        raise ValueError("compare alternatives and explain your choice before submitting")
    if evidence.get("preview_token") != review["preview_token"]:
        raise ValueError("the decision or available resources changed; refresh the comparison")
    if not review["alternatives"] and evidence.get("alternative_id") == "no_feasible_alternative":
        rationale = str(evidence.get("rationale", "")).strip()
        if not 20 <= len(rationale) <= 2000:
            raise ValueError("explain the binding constraint in 20 to 2000 characters")
        return {**review, "foregone": {"id": "no_feasible_alternative", "label": "No different feasible allocation exists",
            "allocation": review["selected"], "commitment": review["assumptions"]["committed"], "remaining": review["assumptions"]["remaining"]},
            "rationale": rationale, "assessment": {"recognized_constraint": True, "compared_feasible_alternative": False,
                "rationale_recorded": True, "quality_requires_instructor_review": True}}
    alternative = next((item for item in review["alternatives"] if item["id"] == evidence.get("alternative_id")), None)
    if alternative is None:
        raise ValueError("select a feasible next-best alternative")
    rationale = str(evidence.get("rationale", "")).strip()
    if len(rationale) < 20 or len(rationale) > 2000:
        raise ValueError("explain your choice in 20 to 2000 characters")
    return {**review, "foregone": alternative, "rationale": rationale,
        "assessment": {"recognized_constraint": True, "compared_feasible_alternative": True,
                       "rationale_recorded": True, "quality_requires_instructor_review": True}}


def readiness_bonus(readiness):
    return min(5, math.floor(math.sqrt(max(0.0, readiness))))


def advisor_prompt_for_review(review):
    """Phase 4 adapter contract; caller must supply an authorized private review."""
    return {
        "instruction": "Ask Socratic questions about the binding constraint, the next unit of spending, and the selected next-best alternative. Distinguish estimates from realized results. Do not choose an allocation or reveal another player's private information.",
        "ruleset_version": RULESET,
        "review": review,
    }
