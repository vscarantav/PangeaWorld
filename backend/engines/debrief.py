"""Read-only, privacy-safe post-game debrief projections."""

REAL_WORLD_CONNECTIONS = {
    "natural_disaster": {"title": "Disaster recovery and fiscal trade-offs", "summary": "Compare recovery funding choices with disaster reconstruction cases, where urgent relief competes with longer-term investment."},
    "market_shock": {"title": "Commodity and market shocks", "summary": "Compare this shock with historical supply disruptions, when households and firms faced changing prices before policy could fully respond."},
    "political_crisis": {"title": "Political confidence crisis", "summary": "Compare changes in confidence and approval with episodes where policy credibility affected economic choices."},
    "health_emergency": {"title": "Public-health disruption", "summary": "Compare this disruption with public-health emergencies that required balancing near-term capacity with economic continuity."},
    "military_attack": {"title": "Conflict and economic spillovers", "summary": "Compare the conflict's price, trade, and readiness effects with how real conflicts disrupt civilian economic life."},
}


def counterfactual_from_review(review):
    """Return the stored alternative as an explicitly non-historical estimate.

    Replaying a prior round against already-mutated game state would be misleading.
    The immutable submission-time assumptions are therefore the authoritative
    counterfactual available in this sprint.
    """
    record = review.record or {}
    assumptions = record.get("assumptions") or {}
    alternative = record.get("foregone") or {}
    if not alternative:
        raise ValueError("this decision has no recorded feasible alternative")
    return {"estimate": True, "label": "Estimated counterfactual — not a guaranteed outcome",
            "selected": {"allocation": record.get("selected", {}), "remaining": assumptions.get("remaining"), "commitment": assumptions.get("committed")},
            "foregone": {"id": alternative.get("id"), "label": alternative.get("label"), "allocation": alternative.get("allocation"), "remaining": alternative.get("remaining"), "commitment": alternative.get("commitment"), "projection": alternative.get("projection", {})},
            "explanation": "This compares the selected decision with the feasible alternative recorded at submission. It does not claim to recreate later events, rival decisions, or market conditions."}
