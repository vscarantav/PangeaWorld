"""Pure, deterministic Phase 3 disaster and readiness resolution."""

from __future__ import annotations

from typing import Any


# Kept deliberately small and visible for the Sprint 1 balancing rehearsal.
DISASTER_DAMAGE_PER_SEVERITY = 300.0
PRIVATE_FINANCING_RATE = 0.15
POSTURE_MITIGATION = {"defend": 0.25, "patrol": 0.15, "reconnaissance": 0.10}
MAX_READINESS_MITIGATION = 0.20


def resolve_natural_disaster(*, event_id: int, event_key: str, severity: int,
                             nation_id: int, posture: str,
                             military_investment: float,
                             public_fund_available: float,
                             company_ids: list[int], round_number: int) -> dict[str, Any]:
    """Resolve one disaster without database access or nondeterministic inputs.

    Public preparedness is allocated before the remaining recovery obligation is
    shared by affected companies in ascending ID order.  The resulting plan can
    therefore be persisted and replayed exactly.
    """
    if severity not in {1, 2, 3}:
        raise ValueError("event severity must be from 1 to 3")
    if posture not in POSTURE_MITIGATION:
        raise ValueError("unsupported military posture")

    readiness_mitigation = min(MAX_READINESS_MITIGATION, max(0.0, float(military_investment)) / 10_000.0)
    gross_impact = round(DISASTER_DAMAGE_PER_SEVERITY * severity * (1.0 - POSTURE_MITIGATION[posture] - readiness_mitigation), 2)
    public_used = round(min(max(0.0, float(public_fund_available)), gross_impact), 2)
    private_total = round(gross_impact - public_used, 2)
    ordered_companies = sorted(set(int(company_id) for company_id in company_ids))
    allocations = []
    if ordered_companies:
        base, remainder = divmod(int(round(private_total * 100)), len(ordered_companies))
        for index, company_id in enumerate(ordered_companies):
            private_amount = (base + (1 if index < remainder else 0)) / 100.0
            allocations.append({
                "company_id": company_id,
                "public_fund_amount": round(public_used / len(ordered_companies), 2),
                "private_fund_amount": private_amount,
                "private_financing_cost": round(private_amount * PRIVATE_FINANCING_RATE, 2),
            })
    elif private_total:
        # No company can be charged; the entire gap remains an economic loss.
        private_total = 0.0

    financing_total = round(sum(item["private_financing_cost"] for item in allocations), 2)
    approval_delta = round(-severity * (0.5 + 1.5 * (private_total / gross_impact if gross_impact else 0.0)), 2)
    reproducibility_key = f"phase3:{round_number}:{event_id}:{event_key}:{nation_id}:{posture}:{military_investment:.2f}:{public_fund_available:.2f}"
    return {
        "event_id": event_id,
        "nation_id": nation_id,
        "gross_impact": gross_impact,
        "public_fund_used": public_used,
        "private_recovery_total": private_total,
        "private_financing_total": financing_total,
        "approval_delta": approval_delta,
        "gdp_delta": round(-(gross_impact + financing_total), 2),
        "military_readiness_delta": round(float(military_investment) / 100.0, 4),
        "allocations": allocations,
        "reproducibility_key": reproducibility_key,
    }


def public_disaster_article(*, event_id: int, round_number: int, nation_name: str,
                            event_title: str, severity: int, public_fund_used: float) -> dict[str, Any]:
    """Return the deterministic, privacy-safe Pangea Times article payload."""
    return {
        "id": f"phase3-{event_id}", "round": round_number, "category": "Disaster",
        "impact": "High" if severity >= 3 else "Moderate",
        "headline": f"{event_title} prompts recovery response in {nation_name}",
        "summary": f"Public recovery resources committed: ${public_fund_used:.2f}M.",
    }
