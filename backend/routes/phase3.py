"""Instructor-only catalog event commands for the Phase 3 vertical slice."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..deadlines import session_mutation_lock
    from ..engines.phase3_contract import validate_event_severity, validate_event_target
    from ..models.domain import EventScope, EventType, Round, RoundEvent, RoundStatus, User
    from ..auth import get_current_user
    from ..realtime import notify_session
    from ..engines.phase3_resolver import public_disaster_article
    from ..engines.phase3_military import public_attack_article
except ImportError:
    from database import get_db
    from deadlines import session_mutation_lock
    from engines.phase3_contract import validate_event_severity, validate_event_target
    from models.domain import EventScope, EventType, Round, RoundEvent, RoundStatus, User
    from auth import get_current_user
    from realtime import notify_session
    from engines.phase3_resolver import public_disaster_article
    from engines.phase3_military import public_attack_article
from .helpers import get_session_or_404, require_assigned_membership, require_instructor


router = APIRouter(prefix="/api/sessions/{session_id}/phase3", tags=["phase3"])

EVENT_CATALOG = {
    "coastal_storm": {"event_type": EventType.NATURAL_DISASTER, "severity": 2, "title": "Coastal storm", "summary": "Storm damage disrupts affected local operations."},
    "major_earthquake": {"event_type": EventType.NATURAL_DISASTER, "severity": 3, "title": "Major earthquake", "summary": "Severe infrastructure damage requires emergency recovery funding."},
}


class CustomScenario(BaseModel):
    model_config = {"extra": "forbid"}
    title: str = Field(min_length=5, max_length=120)
    summary: str = Field(min_length=10, max_length=500)
    event_type: EventType
    severity: int = Field(default=2, ge=1, le=3)
    cpi_delta: float = Field(default=0, ge=-5, le=10, allow_inf_nan=False)
    approval_delta: float = Field(default=0, ge=-10, le=10, allow_inf_nan=False)


class EventInjection(BaseModel):
    scenario: CustomScenario | None = None
    model_config = {"extra": "forbid"}
    catalog_key: str
    target_nation_id: int = Field(gt=0)
    target_round: int | None = Field(default=None, ge=1, le=7)


@router.get("/results")
def phase3_results(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Publish immutable, privacy-safe event results and their news payloads."""
    session = get_session_or_404(db, session_id)
    require_assigned_membership(db, session_id, user.id)
    results = []
    for round_ in sorted(session.rounds, key=lambda item: item.number, reverse=True):
        if round_.status != RoundStatus.COMPLETE:
            continue
        for event in round_.phase3_events:
            effect = next((item for item in round_.effects if item.round_event_id == event.id and item.scope == EventScope.PUBLIC), None)
            if effect is None:
                continue
            nation = next((item for item in session.nations if item.id == event.target_nation_id), None)
            title = (event.event_data or {}).get("title", "Natural disaster")
            public_effects = effect.effect_data or {}
            results.append({
                "round": round_.number, "event_id": event.id, "event_type": event.event_type.value,
                "target_nation_id": event.target_nation_id, "title": title, "severity": event.severity,
                "effects": public_effects,
                "article": public_disaster_article(
                    event_id=event.id, round_number=round_.number,
                    nation_name=nation.name if nation else "the affected nation", event_title=title,
                    severity=event.severity, public_fund_used=float(public_effects.get("public_fund_used", 0.0)),
                ),
            })
        for operation_effect in (item for item in round_.effects if item.scope == EventScope.PUBLIC and item.effect_type == "military_operation"):
            data = operation_effect.effect_data
            results.append({"round": round_.number, "event_id": f"operation-{operation_effect.id}",
                "event_type": "military_operation", "title": "Military operation", "severity": 2,
                "target_nation_id": data["target_id"], "effects": data,
                "article": {"id": f"operation-{operation_effect.id}", "headline": f"Nation {data['attacker_id']} conducts {data['outcome']} against nation {data['target_id']}",
                            "summary": f"Operation cost: ${data['operation_cost']}M."}})
        for effect in sorted((item for item in round_.effects
                              if item.scope == EventScope.PUBLIC and item.effect_type == "military_attack"),
                             key=lambda item: item.id):
            public_effects = effect.effect_data or {}
            attacker = next((item for item in session.nations if item.id == effect.entity_id), None)
            target = next((item for item in session.nations if item.id == public_effects.get("target_id")), None)
            if attacker is None or target is None:
                continue
            results.append({
                "round": round_.number, "event_id": f"combat-{effect.id}", "event_type": "military_attack",
                "target_nation_id": target.id, "attacker_nation_id": attacker.id,
                "title": "Military clash", "severity": 3, "effects": public_effects,
                "article": public_attack_article(
                    effect_id=effect.id, round_number=round_.number, attacker_name=attacker.name,
                    target_name=target.name, outcome=public_effects.get("outcome", "defender_holds"),
                    attacker_losses=int(public_effects.get("attacker_losses", 0)),
                    defender_losses=int(public_effects.get("defender_losses", 0)),
                    control_transferred=int(public_effects.get("control_transferred", 0)),
                ),
            })
    return {"results": results}


@router.get("/event-catalog")
def event_catalog(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_session_or_404(db, session_id); require_instructor(db, session_id, user.id)
    return [{"key": key, "title": value["title"], "summary": value["summary"], "severity": value["severity"]} for key, value in EVENT_CATALOG.items()]


@router.post("/events")
def inject_event(session_id: int, payload: EventInjection, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    with session_mutation_lock(session_id):
        session = get_session_or_404(db, session_id); require_instructor(db, session_id, user.id)
        if session.phase.value not in {"planning", "presidential", "company"}:
            raise HTTPException(status_code=409, detail="events are locked during processing and after completion")
        definition = EVENT_CATALOG.get(payload.catalog_key)
        if payload.catalog_key == "custom" and payload.scenario is not None:
            definition = payload.scenario.model_dump()
        elif payload.scenario is not None:
            raise HTTPException(status_code=422, detail="custom scenario requires the custom catalog key")
        if definition is None:
            raise HTTPException(status_code=422, detail="unknown event catalog key")
        target_round = payload.target_round or session.current_round
        if target_round != session.current_round:
            raise HTTPException(status_code=409, detail="events can only be injected for the active round")
        round_ = db.query(Round).filter_by(session_id=session_id, number=target_round).first()
        if db.query(RoundEvent).filter_by(round_id=round_.id).first() is not None:
            raise HTTPException(status_code=409, detail="only one Phase 3 event may be scheduled per round")
        try:
            validate_event_target(db, round_, definition["event_type"], payload.target_nation_id)
            severity = validate_event_severity(definition["severity"])
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        event = RoundEvent(round_id=round_.id, event_type=definition["event_type"], target_nation_id=payload.target_nation_id,
                           severity=severity, event_data={"catalog_key": payload.catalog_key, "title": definition["title"], "summary": definition.get("summary", ""), "cpi_delta": definition.get("cpi_delta", 0), "approval_delta": definition.get("approval_delta", 0)}, injected_by_user_id=user.id)
        db.add(event)
        try:
            db.commit(); db.refresh(event)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="an equivalent event is already scheduled for this nation and round") from exc
        notify_session(session_id, "event_scheduled", round=target_round)
        return {"id": event.id, "round": target_round, "catalog_key": payload.catalog_key, "target_nation_id": event.target_nation_id, "severity": severity}


@router.get("/decision-reviews")
def decision_reviews(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        from ..models.domain import DecisionReview
    except ImportError:
        from models.domain import DecisionReview
    session = get_session_or_404(db, session_id)
    member = require_assigned_membership(db, session_id, user.id)
    query = db.query(DecisionReview).join(Round).filter(Round.session_id == session_id)
    if member.role != "instructor":
        query = query.filter(DecisionReview.player_type == ("president" if member.role == "president" else "company"),
                             DecisionReview.entity_id == member.entity_id)
    reviews = []
    latest_seen = set()
    for row in query.order_by(DecisionReview.id.desc()).all():
        round_ = next(item for item in session.rounds if item.id == row.round_id)
        identity = (row.round_id, row.player_type, row.entity_id)
        superseded = identity in latest_seen
        latest_seen.add(identity)
        feedback = None
        if round_.status == RoundStatus.COMPLETE and not superseded:
            key, id_key = ("nations", "nation_id") if row.player_type == "president" else ("companies", "company_id")
            outcome = next((item for item in (round_.results or {}).get(key, []) if item[id_key] == row.entity_id), {})
            feedback = {"realized": outcome,
                "foregone_allocation": row.record["foregone"],
                "comparison": "The alternative's remaining funds are a submission-time estimate, not a simulated historical outcome. Military losses, events, supplier competition and market responses were unknown.",
                "resource_remaining_difference_at_submission": round(row.record["foregone"]["remaining"] - row.record["assumptions"]["remaining"], 4)}
        reviews.append({"id": row.id, "round": round_.number, "player_type": row.player_type,
            "entity_id": row.entity_id, "superseded": superseded, "record": row.record, "feedback": feedback})
    try:
        from ..models.domain import RoundEffect
    except ImportError:
        from models.domain import RoundEffect
    reports = db.query(RoundEffect).join(Round).filter(Round.session_id == session_id,
        Round.status == RoundStatus.COMPLETE, RoundEffect.effect_type == "intelligence_report")
    if member.role != "instructor":
        reports = reports.filter(RoundEffect.entity_id == member.entity_id) if member.role == "president" else reports.filter(False)
    return {"reviews": reviews, "intelligence_reports": [{"id": item.id, **item.effect_data} for item in reports.all()]}


@router.get("/opportunity-cost-scorecard")
def opportunity_cost_scorecard(session_id: int, db: Session = Depends(get_db),
                               user: User = Depends(get_current_user)):
    """Aggregate evidence for instructor review without assigning an automatic grade."""
    try:
        from ..models.domain import DecisionReview
    except ImportError:
        from models.domain import DecisionReview
    get_session_or_404(db, session_id)
    require_instructor(db, session_id, user.id)
    rows = (db.query(DecisionReview).join(Round)
            .filter(Round.session_id == session_id)
            .order_by(DecisionReview.created_at, DecisionReview.id).all())
    grouped = {}
    for row in rows:
        key = (row.player_type, row.entity_id)
        entry = grouped.setdefault(key, {
            "player_type": row.player_type,
            "entity_id": row.entity_id,
            "submissions_reviewed": 0,
            "rounds_participated": set(),
            "constraints_recognized": 0,
            "feasible_alternatives_compared": 0,
            "rationale_characters": [],
        })
        record = row.record or {}
        assessment = record.get("assessment") or {}
        entry["submissions_reviewed"] += 1
        entry["rounds_participated"].add(row.round_id)
        entry["constraints_recognized"] += int(bool(assessment.get("recognized_constraint")))
        entry["feasible_alternatives_compared"] += int(bool(assessment.get("compared_feasible_alternative")))
        entry["rationale_characters"].append(len(str(record.get("rationale", ""))))
    scorecards = []
    for entry in grouped.values():
        count = entry["submissions_reviewed"]
        rationale_lengths = entry.pop("rationale_characters")
        rounds = entry.pop("rounds_participated")
        scorecards.append({
            **entry,
            "rounds_participated": len(rounds),
            "constraint_recognition_rate": round(entry["constraints_recognized"] / count, 4),
            "feasible_comparison_rate": round(entry["feasible_alternatives_compared"] / count, 4),
            "average_rationale_characters": round(sum(rationale_lengths) / count, 2),
            "revision_count": count - len(rounds),
            "quality_requires_instructor_review": True,
        })
    return {"scorecards": sorted(scorecards, key=lambda item: (item["player_type"], item["entity_id"]))}


class Phase3Settings(BaseModel):
    model_config = {"extra": "forbid"}
    drakmoor_mode: str = Field(pattern="^(scripted|passive)$")


@router.get("/settings")
def get_phase3_settings(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = get_session_or_404(db, session_id)
    require_instructor(db, session_id, user.id)
    return {"drakmoor_mode": (session.phase3_settings or {}).get("drakmoor_mode", "scripted")}


@router.put("/settings")
def set_phase3_settings(session_id: int, payload: Phase3Settings, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    with session_mutation_lock(session_id):
        session = get_session_or_404(db, session_id)
        require_instructor(db, session_id, user.id)
        if session.phase.value != "planning":
            raise HTTPException(status_code=409, detail="behavior can only change during planning")
        settings = dict(session.phase3_settings or {})
        history = list(settings.get("history", []))
        history.append({"round": session.current_round, "user_id": user.id, "drakmoor_mode": payload.drakmoor_mode})
        session.phase3_settings = {"drakmoor_mode": payload.drakmoor_mode, "history": history}
        db.commit()
        return {"drakmoor_mode": payload.drakmoor_mode}
