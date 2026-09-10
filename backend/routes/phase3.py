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
except ImportError:
    from database import get_db
    from deadlines import session_mutation_lock
    from engines.phase3_contract import validate_event_severity, validate_event_target
    from models.domain import EventScope, EventType, Round, RoundEvent, RoundStatus, User
    from auth import get_current_user
    from realtime import notify_session
    from engines.phase3_resolver import public_disaster_article
from .helpers import get_session_or_404, require_assigned_membership, require_instructor


router = APIRouter(prefix="/api/sessions/{session_id}/phase3", tags=["phase3"])

EVENT_CATALOG = {
    "coastal_storm": {"event_type": EventType.NATURAL_DISASTER, "severity": 2, "title": "Coastal storm", "summary": "Storm damage disrupts affected local operations."},
    "major_earthquake": {"event_type": EventType.NATURAL_DISASTER, "severity": 3, "title": "Major earthquake", "summary": "Severe infrastructure damage requires emergency recovery funding."},
}


class EventInjection(BaseModel):
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
    return {"results": results}


@router.get("/event-catalog")
def event_catalog(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_session_or_404(db, session_id); require_instructor(db, session_id, user.id)
    return [{"key": key, "title": value["title"], "summary": value["summary"], "severity": value["severity"]} for key, value in EVENT_CATALOG.items()]


@router.post("/events")
def inject_event(session_id: int, payload: EventInjection, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    with session_mutation_lock(session_id):
        session = get_session_or_404(db, session_id); require_instructor(db, session_id, user.id)
        definition = EVENT_CATALOG.get(payload.catalog_key)
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
                           severity=severity, event_data={"catalog_key": payload.catalog_key, "title": definition["title"]}, injected_by_user_id=user.id)
        db.add(event)
        try:
            db.commit(); db.refresh(event)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="an equivalent event is already scheduled for this nation and round") from exc
        notify_session(session_id, "event_scheduled", round=target_round)
        return {"id": event.id, "round": target_round, "catalog_key": payload.catalog_key, "target_nation_id": event.target_nation_id, "severity": severity}
