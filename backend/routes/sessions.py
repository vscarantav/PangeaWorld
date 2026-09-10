from copy import deepcopy
from datetime import timedelta
import re

from fastapi import APIRouter, Depends, HTTPException, status
import secrets
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

try:
    from ..database import get_db
    from ..deadlines import active_deadline, as_utc, deadline_has_passed, session_mutation_lock, utc_now
    from ..engines.round_manager import advance_phase, apply_auto_decisions
    from ..models.domain import Company, Decision, DecisionDraft, GameMembership, GameSession, LobbyAudit, Nation, PhaseEnum, Round, User
    from ..auth import get_current_user
    from ..moderation import is_classroom_safe_name
    from ..realtime import notify_session
    from ..seed_data import seed_game_session
except ImportError:
    from database import get_db
    from deadlines import active_deadline, as_utc, deadline_has_passed, session_mutation_lock, utc_now
    from engines.round_manager import advance_phase, apply_auto_decisions
    from models.domain import Company, Decision, DecisionDraft, GameMembership, GameSession, LobbyAudit, Nation, PhaseEnum, Round, User
    from auth import get_current_user
    from moderation import is_classroom_safe_name
    from realtime import notify_session
    from seed_data import seed_game_session
from .helpers import get_session_or_404, require_assigned_membership, require_instructor, require_membership
try:
    from ..map_snapshots import normalize_map_snapshot
    from ..models.domain import MapSnapshot
except ImportError:
    from map_snapshots import normalize_map_snapshot
    from models.domain import MapSnapshot

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

class SessionCreate(BaseModel):
    model_config = {"extra": "forbid"}
    phase_duration_seconds: int = Field(default=172800, ge=1, le=172800)


class AdvanceRequest(BaseModel):
    expected_phase: PhaseEnum


class MapUpdate(BaseModel):
    map_snapshot: dict


class LobbyJoin(BaseModel):
    join_code: str = Field(min_length=6, max_length=32)


class SeatAssignment(BaseModel):
    user_id: int
    role: str = Field(pattern="^(president|executive)$")
    entity_id: int


class RenamePayload(BaseModel):
    name: str = Field(min_length=2, max_length=60, pattern=r"^[A-Za-z0-9 .,'&-]+$")


def _membership_or_403(db, session_id, user_id):
    membership = db.query(GameMembership).filter_by(session_id=session_id, user_id=user_id).first()
    if membership is None:
        raise HTTPException(status_code=403, detail="not a member of this game")
    return membership


def _instructor_or_403(db, session_id, user_id):
    membership = _membership_or_403(db, session_id, user_id)
    if membership.role != "instructor":
        raise HTTPException(status_code=403, detail="instructor role required")
    return membership


def _new_join_code(db):
    while True:
        code = secrets.token_urlsafe(6).upper().replace("-", "").replace("_", "")[:10]
        if not db.query(GameSession).filter_by(lobby_join_code=code).first():
            return code


def _has_renderable_map_snapshot(session):
    snapshot = session.map_snapshot
    return bool(
        isinstance(snapshot, dict)
        and snapshot.get("triangles")
        and snapshot.get("edges")
        and snapshot.get("countries")
        and "cities" in snapshot
        and all(len(triangle.get("points", [])) == 3 for triangle in snapshot["triangles"])
        and all(
            (edge.get("p1") and edge.get("p2"))
            or re.fullmatch(r"-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?--?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?", str(edge.get("id", "")))
            for edge in snapshot["edges"]
        )
    )


def _member_view(membership):
    return {"id": membership.id, "user_id": membership.user_id,
            "display_name": membership.user.display_name or membership.user.email,
            "role": membership.role, "entity_id": membership.entity_id,
            "joined_at": membership.joined_at}

@router.post("")
def create_session(payload: SessionCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.is_instructor:
        raise HTTPException(status_code=403, detail="instructor account required to create a game")
    session_seed = secrets.token_urlsafe(18)
    session = GameSession(seed=session_seed, phase=PhaseEnum.PLANNING, status="lobby",
                          lobby_join_code=_new_join_code(db), phase_duration_seconds=payload.phase_duration_seconds)
    db.add(session)
    db.flush()
    seed_game_session(db, session.id, commit=False)
    db.add(GameMembership(session_id=session.id, user_id=user.id, role="instructor"))
    db.commit()
    return _session_view(session)


@router.get("/lobby/{join_code}")
def public_lobby(join_code: str, db: Session = Depends(get_db)):
    session = db.query(GameSession).filter_by(lobby_join_code=join_code.upper()).first()
    if session is None or session.lobby_code_revoked or session.status != "lobby":
        raise HTTPException(status_code=404, detail="lobby not found or closed")
    return {"id": session.id, "join_code": session.lobby_join_code, "status": session.status,
            "member_count": len(session.memberships)}


@router.get("/legacy/recoverable")
def recoverable_legacy_sessions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.is_instructor:
        raise HTTPException(status_code=403, detail="instructor account required")
    sessions = db.query(GameSession).filter(GameSession.lobby_join_code.is_(None)).all()
    return [{"id": session.id, "seed": session.seed, "status": session.status,
             "phase": session.phase.value, "current_round": session.current_round,
             "has_map_snapshot": _has_renderable_map_snapshot(session)}
            for session in sessions if not session.memberships]


@router.post("/lobby/join")
def join_lobby(payload: LobbyJoin, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = db.query(GameSession).filter_by(lobby_join_code=payload.join_code.strip().upper()).first()
    if session is None or session.lobby_code_revoked or session.status != "lobby":
        raise HTTPException(status_code=404, detail="lobby not found or closed")
    membership = db.query(GameMembership).filter_by(session_id=session.id, user_id=user.id).first()
    if membership is None:
        membership = GameMembership(session_id=session.id, user_id=user.id, role="player")
        db.add(membership)
        db.commit()
        db.refresh(membership)
        notify_session(session.id, "lobby_changed", membership_id=membership.id)
    return {"session_id": session.id, "membership": _member_view(membership)}


@router.get("/{session_id}/lobby")
def get_lobby(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = get_session_or_404(db, session_id)
    _membership_or_403(db, session_id, user.id)
    response = {"session_id": session.id, "status": session.status,
                "my_membership": _member_view(_membership_or_403(db, session_id, user.id))}
    if response["my_membership"]["role"] == "instructor":
        occupied = {(item.role, item.entity_id) for item in session.memberships if item.entity_id is not None}
        response.update({"join_code": None if session.lobby_code_revoked else session.lobby_join_code,
                         "seed": session.seed, "has_map_snapshot": _has_renderable_map_snapshot(session),
                         "members": [_member_view(item) for item in session.memberships],
                         "seats": {"nations": [{"id": n.id, "name": n.name, "occupied": ("president", n.id) in occupied} for n in session.nations],
                                   "companies": [{"id": c.id, "name": c.name, "nation_id": c.nation_id, "occupied": ("executive", c.id) in occupied}
                                                 for n in session.nations for c in n.companies]}})
    return response


@router.post("/{session_id}/lobby/assign")
def assign_seat(session_id: int, payload: SeatAssignment, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = get_session_or_404(db, session_id)
    _instructor_or_403(db, session_id, user.id)
    if session.status != "lobby":
        raise HTTPException(status_code=409, detail="seats can only be assigned while the lobby is open")
    membership = db.query(GameMembership).filter_by(session_id=session_id, user_id=payload.user_id).first()
    if membership is None or membership.role == "instructor":
        raise HTTPException(status_code=404, detail="join the lobby before receiving a player seat")
    valid = (db.query(Nation).filter_by(id=payload.entity_id, session_id=session_id).first() if payload.role == "president"
             else db.query(Company).join(Nation).filter(Company.id == payload.entity_id, Nation.session_id == session_id).first())
    if valid is None:
        raise HTTPException(status_code=422, detail="seat entity does not belong to this game")
    occupied = db.query(GameMembership).filter_by(session_id=session_id, role=payload.role, entity_id=payload.entity_id).first()
    if occupied and occupied.id != membership.id:
        raise HTTPException(status_code=409, detail="seat is already assigned")
    membership.role, membership.entity_id = payload.role, payload.entity_id
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="seat is already assigned") from exc
    db.refresh(membership)
    notify_session(session_id, "assignment_changed", membership_id=membership.id)
    return {"membership": _member_view(membership)}


@router.delete("/{session_id}/lobby/members/{user_id}")
def remove_member(session_id: int, user_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = get_session_or_404(db, session_id)
    _instructor_or_403(db, session_id, user.id)
    if session.status != "lobby": raise HTTPException(status_code=409, detail="lobby is closed")
    membership = db.query(GameMembership).filter_by(session_id=session_id, user_id=user_id).first()
    if membership is None or membership.role == "instructor": raise HTTPException(status_code=404, detail="player membership not found")
    membership_id = membership.id
    db.delete(membership); db.commit()
    notify_session(session_id, "assignment_changed", membership_id=membership_id)
    return {"removed": True}


@router.post("/{session_id}/lobby/revoke-code")
def revoke_join_code(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = get_session_or_404(db, session_id); _instructor_or_403(db, session_id, user.id)
    session.lobby_code_revoked = 1; db.commit()
    notify_session(session_id, "lobby_changed")
    return {"revoked": True}


@router.post("/{session_id}/lobby/start")
def start_game(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = get_session_or_404(db, session_id); _instructor_or_403(db, session_id, user.id)
    if session.status != "lobby": raise HTTPException(status_code=409, detail="game has already started")
    if not _has_renderable_map_snapshot(session) or not db.query(MapSnapshot).filter_by(session_id=session_id).first():
        raise HTTPException(status_code=409, detail="persist a validated starting map before starting the game")
    session.status = "active"; session.lobby_code_revoked = 1; db.commit()
    notify_session(session_id, "phase_changed", round=session.current_round, phase=session.phase.value)
    return _session_view(session)


def _rename_authorized(membership, entity_id, role):
    return membership.role == "instructor" or (membership.role == role and membership.entity_id == entity_id)


def _rename(session_id, entity_id, payload, role, db, user):
    session = get_session_or_404(db, session_id)
    membership = _membership_or_403(db, session_id, user.id)
    if session.current_round != 1:
        raise HTTPException(status_code=409, detail="names can only be changed during Round 1")
    entity = (db.query(Nation).filter_by(id=entity_id, session_id=session_id).first() if role == "president"
              else db.query(Company).join(Nation).filter(Company.id == entity_id, Nation.session_id == session_id).first())
    if entity is None:
        raise HTTPException(status_code=404, detail="entity not found in this game")
    if not _rename_authorized(membership, entity_id, role):
        raise HTTPException(status_code=403, detail="only the assigned seat or instructor can rename this entity")
    new_name = payload.name.strip()
    if len(new_name) < 2:
        raise HTTPException(status_code=422, detail="name must contain at least two non-space characters")
    if new_name.casefold() in {"admin", "administrator", "moderator", "pangeaworld"}:
        raise HTTPException(status_code=422, detail="name is reserved")
    if not is_classroom_safe_name(new_name):
        raise HTTPException(status_code=422, detail="name is not appropriate for a classroom game")
    query = db.query(type(entity)).filter(type(entity).name.ilike(new_name))
    if role == "president":
        query = query.filter(Nation.session_id == session_id)
    else:
        query = query.join(Nation).filter(Nation.session_id == session_id)
    duplicate = query.filter(type(entity).id != entity_id).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="name is already in use in this game")
    old_name = entity.name
    entity.name = new_name
    if role == "president" and session.map_snapshot:
        snapshot = deepcopy(session.map_snapshot)
        for country in snapshot.get("countries", []):
            if str(country.get("name", "")).casefold() == old_name.casefold():
                country["name"] = new_name
        session.map_snapshot = snapshot
        stored = db.query(MapSnapshot).filter_by(session_id=session.id).first()
        if stored is not None:
            stored.validated_map_json = snapshot
    db.add(LobbyAudit(session_id=session_id, actor_user_id=user.id, action="rename", entity_type=role,
                      entity_id=entity_id, before_value=old_name, after_value=new_name))
    db.commit()
    notify_session(session_id, "name_changed", entity_type=role, entity_id=entity_id)
    return {"id": entity.id, "name": entity.name}


@router.put("/{session_id}/nations/{nation_id}/name")
def rename_nation(session_id: int, nation_id: int, payload: RenamePayload, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _rename(session_id, nation_id, payload, "president", db, user)


@router.put("/{session_id}/companies/{company_id}/name")
def rename_company(session_id: int, company_id: int, payload: RenamePayload, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _rename(session_id, company_id, payload, "executive", db, user)

def _session_view(session):
    return {"id": session.id, "seed": session.seed, "current_round": session.current_round,
            "phase": session.phase.value, "status": session.status, "map_snapshot": session.map_snapshot,
            "server_time": utc_now().isoformat(),
            "presidential_deadline_at": as_utc(session.presidential_deadline_at),
            "company_deadline_at": as_utc(session.company_deadline_at),
            "phase_duration_seconds": session.phase_duration_seconds,
            "rounds": [{"id": r.id, "number": r.number, "status": r.status.value, "events": r.events or [], "results": r.results or {}} for r in session.rounds]}


@router.get("/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = get_session_or_404(db, session_id)
    require_assigned_membership(db, session_id, user.id)
    return _session_view(session)


@router.put("/{session_id}/map")
def update_map(session_id: int, payload: MapUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = get_session_or_404(db, session_id)
    require_instructor(db, session_id, user.id)
    if session.status != "lobby" or session.current_round != 1:
        raise HTTPException(status_code=409, detail="the starting map is frozen after the game begins")
    try:
        snapshot = normalize_map_snapshot(payload.map_snapshot)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if snapshot["seed"] != session.seed:
        raise HTTPException(status_code=422, detail="map_snapshot.seed must match session seed")
    session.map_snapshot = snapshot
    stored = db.query(MapSnapshot).filter_by(session_id=session.id).first()
    if stored is None:
        stored = MapSnapshot(session_id=session.id, validated_map_json=snapshot)
        db.add(stored)
    else:
        stored.validated_map_json = snapshot
    db.commit()
    notify_session(session_id, "map_changed")
    return {"session_id": session.id, "map_snapshot": snapshot}

def _record_deadline_autos(db, session):
    role = "president" if session.phase == PhaseEnum.PRESIDENTIAL else "executive"
    player_type = "president" if role == "president" else "company"
    round_ = db.query(Round).filter_by(session_id=session.id, number=session.current_round).one()
    submitted = {decision.entity_id for decision in round_.decisions if decision.player_type == player_type}
    missing = [membership for membership in session.memberships
               if membership.role == role and membership.entity_id is not None and membership.entity_id not in submitted]
    if missing and not deadline_has_passed(session):
        raise ValueError(f"{role} seats are still pending and the phase deadline has not passed")
    entity_model = Nation if role == "president" else Company
    for membership in missing:
        entity = db.query(entity_model).filter_by(id=membership.entity_id).one()
        db.add(Decision(round_id=round_.id, player_type=player_type, entity_id=membership.entity_id,
                        decision_data=apply_auto_decisions(entity, player_type), submission_kind="auto",
                        auto_reason="deadline_expired"))
        db.query(DecisionDraft).filter_by(round_id=round_.id, player_type=player_type, entity_id=membership.entity_id).delete()


def _advance_session_locked(session_id, expected_phase, db, user):
    session = db.query(GameSession).filter_by(id=session_id).with_for_update().first()
    if session is None:
        raise HTTPException(status_code=404, detail="game session not found")
    require_instructor(db, session_id, user.id)
    if session.status != "active":
        raise HTTPException(status_code=409, detail="start the game before advancing phases")
    if session.phase != expected_phase:
        return {"phase": session.phase.value, "round": session.current_round, "processed": False, "idempotent": True}
    try:
        if session.phase in {PhaseEnum.PRESIDENTIAL, PhaseEnum.COMPANY}:
            _record_deadline_autos(db, session)
        result = advance_phase(db, session, commit=False)
        now = utc_now()
        if session.phase == PhaseEnum.PRESIDENTIAL:
            session.presidential_deadline_at = now + timedelta(seconds=session.phase_duration_seconds)
        elif session.phase == PhaseEnum.COMPANY:
            session.company_deadline_at = now + timedelta(seconds=session.phase_duration_seconds)
        if result.get("processed"):
            session.presidential_deadline_at = None
            session.company_deadline_at = None
        db.commit()
        event_type = "results_published" if result.get("processed") else "phase_changed"
        notify_session(session_id, event_type, round=session.current_round, phase=session.phase.value,
                       processed=bool(result.get("processed")))
        return result
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{session_id}/advance")
def advance_session(session_id: int, payload: AdvanceRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # PostgreSQL's row lock protects multi-process deployments; this process-local
    # lock also gives SQLite and local classrooms the same exactly-once behavior.
    with session_mutation_lock(session_id):
        return _advance_session_locked(session_id, payload.expected_phase, db, user)

@router.get("/{session_id}/news")
def get_news(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = get_session_or_404(db, session_id)
    require_assigned_membership(db, session_id, user.id)
    articles = []
    for round_ in sorted(session.rounds, key=lambda item: item.number, reverse=True):
        for event in reversed(round_.events or []):
            articles.append({"id": event["id"], "round": round_.number, "headline": event["headline"],
                             "category": event["category"], "impact": event["impact"], "nation_id": event["nation_id"]})
    return {"articles": articles}


@router.get("/{session_id}/readiness")
def readiness(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = get_session_or_404(db, session_id)
    requester = require_assigned_membership(db, session_id, user.id)
    round_ = db.query(Round).filter_by(session_id=session_id, number=session.current_round).first()
    decisions = {(item.player_type, item.entity_id): item for item in (round_.decisions if round_ else [])}
    drafts = {(item.player_type, item.entity_id) for item in db.query(DecisionDraft).filter_by(round_id=round_.id).all()} if round_ else set()
    seats = [membership for membership in session.memberships if membership.role in {"president", "executive"} and membership.entity_id]
    entries = [{"role": membership.role, "entity_id": membership.entity_id,
                "status": ("auto_submitted" if decisions[(("company" if membership.role == "executive" else membership.role), membership.entity_id)].submission_kind == "auto" else "submitted") if (("company" if membership.role == "executive" else membership.role), membership.entity_id) in decisions else
                          "draft" if (("company" if membership.role == "executive" else membership.role), membership.entity_id) in drafts else "not_started"}
               for membership in seats]
    if requester.role != "instructor":
        own = next((item for item in entries if item["role"] == requester.role and item["entity_id"] == requester.entity_id), None)
        return {"round": session.current_round, "phase": session.phase.value, "my_status": own["status"] if own else "unassigned",
                "server_time": utc_now().isoformat(), "deadline_at": active_deadline(session)}
    return {"round": session.current_round, "phase": session.phase.value,
            "submitted": sum(item["status"] in {"submitted", "auto_submitted"} for item in entries), "total": len(entries), "seats": entries,
            "server_time": utc_now().isoformat(), "deadline_at": active_deadline(session)}


@router.post("/{session_id}/claim-legacy")
def claim_legacy_session(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Give a local instructor a controlled recovery path for pre-membership games."""
    session = get_session_or_404(db, session_id)
    if not user.is_instructor:
        raise HTTPException(status_code=403, detail="instructor account required to claim a legacy game")
    if session.memberships or session.lobby_join_code is not None:
        raise HTTPException(status_code=409, detail="only unmigrated Phase 1 sessions can be claimed")
    db.add(GameMembership(session_id=session_id, user_id=user.id, role="instructor"))
    requires_map_rebuild = not _has_renderable_map_snapshot(session)
    if requires_map_rebuild:
        session.status = "lobby"
        session.lobby_join_code = _new_join_code(db)
        session.lobby_code_revoked = 0
    elif not db.query(MapSnapshot).filter_by(session_id=session.id).first():
        db.add(MapSnapshot(session_id=session.id, validated_map_json=session.map_snapshot))
    if not session.nations:
        seed_game_session(db, session.id, commit=False)
    db.commit()
    return {"claimed": True, "requires_map_rebuild": requires_map_rebuild, "session": _session_view(session)}
