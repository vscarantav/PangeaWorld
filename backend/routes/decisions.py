from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from ..deadlines import deadline_has_passed, session_mutation_lock
    from ..database import get_db
    from ..engines.round_manager import submit_decision
    from ..models.schemas import CompanyDecisionData, PresidentDecisionData, PresidentialReadinessData
    from ..models.domain import Decision, DecisionDraft, GameSession, Round, User
    from ..auth import get_current_user
    from ..realtime import notify_session
except ImportError:
    from deadlines import deadline_has_passed, session_mutation_lock
    from database import get_db
    from engines.round_manager import submit_decision
    from models.schemas import CompanyDecisionData, PresidentDecisionData, PresidentialReadinessData
    from models.domain import Decision, DecisionDraft, GameSession, Round, User
    from auth import get_current_user
    from realtime import notify_session
from .helpers import require_membership

router = APIRouter(prefix="/api/sessions/{session_id}", tags=["decisions"])

class PresidentDecisionPayload(BaseModel):
    decision_data: PresidentDecisionData = Field(default_factory=PresidentDecisionData)


class CompanyDecisionPayload(BaseModel):
    decision_data: CompanyDecisionData = Field(default_factory=CompanyDecisionData)


class PresidentialReadinessPayload(BaseModel):
    decision_data: PresidentialReadinessData = Field(default_factory=PresidentialReadinessData)

def _owned_session(session_id: int, entity_id: int, player_type: str, db: Session, user: User):
    session = db.query(GameSession).filter_by(id=session_id).with_for_update().first()
    if session is None:
        raise HTTPException(status_code=404, detail="game session not found")
    membership = require_membership(db, session_id, user.id)
    expected_role = "president" if player_type == "president" else "executive"
    if membership.role != expected_role or membership.entity_id != entity_id:
        raise HTTPException(status_code=403, detail="you do not own this decision seat")
    return session


def _submit_locked(session_id: int, entity_id: int, player_type: str, payload, db: Session, user: User):
    session = _owned_session(session_id, entity_id, player_type, db, user)
    if deadline_has_passed(session):
        raise HTTPException(status_code=409, detail="the phase deadline has passed")
    decision_data = payload.decision_data.model_dump(exclude_none=True)
    # The policy form and the Phase 3 readiness form save separate parts of
    # the same presidential decision.  Pydantic supplies readiness defaults
    # for a policy-only payload, so preserve the already-saved values unless
    # the caller explicitly included a readiness field.
    if player_type == "president":
        round_ = db.query(Round).filter_by(session_id=session_id, number=session.current_round).first()
        existing = db.query(Decision).filter_by(round_id=round_.id, player_type="president", entity_id=entity_id).first()
        if existing:
            explicit_fields = payload.decision_data.model_fields_set
            for field in ("military_posture", "military_investment", "emergency_preparedness_investment",
                          "military_procurement", "military_operation"):
                if field not in explicit_fields and field in (existing.decision_data or {}):
                    decision_data[field] = existing.decision_data[field]
    try:
        decision = submit_decision(db, session, player_type, entity_id, decision_data)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    round_ = db.query(Round).filter_by(session_id=session_id, number=session.current_round).first()
    db.query(DecisionDraft).filter_by(round_id=round_.id, player_type=player_type, entity_id=entity_id).delete()
    db.commit()
    notify_session(session_id, "readiness_changed", round=session.current_round)
    return {"id": decision.id, "round_id": decision.round_id, "player_type": decision.player_type,
            "entity_id": decision.entity_id, "decision_data": decision.decision_data}


def _submit(session_id: int, entity_id: int, player_type: str, payload, db: Session, user: User):
    with session_mutation_lock(session_id):
        return _submit_locked(session_id, entity_id, player_type, payload, db, user)

@router.post("/nations/{nation_id}/decisions")
def submit_presidential_decision(session_id: int, nation_id: int, payload: PresidentDecisionPayload, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _submit(session_id, nation_id, "president", payload, db, user)

@router.post("/companies/{company_id}/decisions")
def submit_company_decision(session_id: int, company_id: int, payload: CompanyDecisionPayload, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _submit(session_id, company_id, "company", payload, db, user)


@router.put("/nations/{nation_id}/readiness")
def save_presidential_readiness(session_id: int, nation_id: int, payload: PresidentialReadinessPayload, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Merge Phase 3 readiness inputs into the President's canonical decision."""
    with session_mutation_lock(session_id):
        session = _owned_session(session_id, nation_id, "president", db, user)
        if deadline_has_passed(session):
            raise HTTPException(status_code=409, detail="the phase deadline has passed")
        round_ = db.query(Round).filter_by(session_id=session_id, number=session.current_round).first()
        existing = db.query(Decision).filter_by(round_id=round_.id, player_type="president", entity_id=nation_id).first()
        merged = dict(existing.decision_data or {}) if existing else {}
        # Only replace military fields the client actually supplied.  This is
        # important when a player edits preparedness after saving an attack
        # order: schema defaults must not silently clear that order.
        # Preserve an explicitly supplied null so a President can withdraw a
        # previously saved attack order; omitted fields still leave the saved
        # readiness plan intact.
        merged.update(payload.decision_data.model_dump(exclude_unset=True))
        try:
            decision = submit_decision(db, session, "president", nation_id, merged)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        notify_session(session_id, "readiness_changed", round=session.current_round)
        return {"id": decision.id, "round_id": decision.round_id, "decision_data": decision.decision_data}


def _save_draft_locked(session_id: int, entity_id: int, player_type: str, payload, db: Session, user: User):
    session = _owned_session(session_id, entity_id, player_type, db, user)
    if deadline_has_passed(session):
        raise HTTPException(status_code=409, detail="the phase deadline has passed")
    expected_phase = "presidential" if player_type == "president" else "company"
    if session.phase.value != expected_phase:
        raise HTTPException(status_code=409, detail=f"{player_type} drafts are locked during {session.phase.value}")
    round_ = db.query(Round).filter_by(session_id=session_id, number=session.current_round).first()
    draft = db.query(DecisionDraft).filter_by(round_id=round_.id, player_type=player_type, entity_id=entity_id).first()
    if draft is None:
        draft = DecisionDraft(round_id=round_.id, player_type=player_type, entity_id=entity_id)
        db.add(draft)
    draft.decision_data = payload.decision_data.model_dump(exclude_none=True)
    db.commit(); db.refresh(draft)
    notify_session(session_id, "readiness_changed", round=session.current_round)
    return {"id": draft.id, "round_id": draft.round_id, "status": "draft"}


def _save_draft(session_id: int, entity_id: int, player_type: str, payload, db: Session, user: User):
    with session_mutation_lock(session_id):
        return _save_draft_locked(session_id, entity_id, player_type, payload, db, user)


@router.put("/nations/{nation_id}/draft")
def save_presidential_draft(session_id: int, nation_id: int, payload: PresidentDecisionPayload, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _save_draft(session_id, nation_id, "president", payload, db, user)


@router.put("/companies/{company_id}/draft")
def save_company_draft(session_id: int, company_id: int, payload: CompanyDecisionPayload, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _save_draft(session_id, company_id, "company", payload, db, user)


class ReviewPreviewPayload(BaseModel):
    decision_data: dict
    readiness_only: bool = False


@router.post("/decision-review/{player_type}/{entity_id}")
def preview_review(session_id: int, player_type: str, entity_id: int, payload: ReviewPreviewPayload,
                   db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        from ..engines.round_manager import preview_decision
        from ..models.domain import Nation, Company
    except ImportError:
        from engines.round_manager import preview_decision
        from models.domain import Nation, Company
    if player_type not in {"president", "company"}:
        raise HTTPException(status_code=422, detail="unsupported decision role")
    session = _owned_session(session_id, entity_id, player_type, db, user)
    if deadline_has_passed(session):
        raise HTTPException(status_code=409, detail="the phase deadline has passed")
    expected_phase = "presidential" if player_type == "president" else "company"
    if session.phase.value != expected_phase:
        raise HTTPException(status_code=409, detail=f"{player_type} reviews are locked during {session.phase.value}")
    data = dict(payload.decision_data)
    if player_type == "president":
        round_ = db.query(Round).filter_by(session_id=session_id, number=session.current_round).first()
        existing = db.query(Decision).filter_by(round_id=round_.id, player_type=player_type, entity_id=entity_id).first()
        previous = dict(existing.decision_data or {}) if existing else {}
        if payload.readiness_only:
            data = {**previous, **data}
        else:
            for field in ("military_posture", "military_investment", "emergency_preparedness_investment", "military_procurement", "military_operation"):
                if field not in data and field in previous:
                    data[field] = previous[field]
    entity = db.get(Nation if player_type == "president" else Company, entity_id)
    try:
        return preview_decision(db, session, player_type, entity, data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
