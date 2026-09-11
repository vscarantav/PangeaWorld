"""Read-only instructor analytics built from persisted game and AI records."""
import csv
import io
import json
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

try:
    from ..auth import get_current_user
    from ..database import get_db
    from ..engines.grading import grade_usage
    from ..models.ai_chat import AIUsageLog
    from ..models.domain import Decision, DecisionReview, GameMembership, Round, User
except ImportError:
    from auth import get_current_user
    from database import get_db
    from engines.grading import grade_usage
    from models.ai_chat import AIUsageLog
    from models.domain import Decision, DecisionReview, GameMembership, Round, User
from .helpers import get_session_or_404, require_instructor

router = APIRouter(prefix="/api/sessions/{session_id}/analytics", tags=["analytics"])


def _members(db, session_id):
    return (db.query(GameMembership).filter(GameMembership.session_id == session_id, GameMembership.role.in_(("president", "executive"))).all())


def _seat_name(member):
    return member.user.display_name or member.user.email


def engagement_data(db, session_id):
    rows = []
    for member in _members(db, session_id):
        role = member.role
        decisions = (db.query(Decision).join(Round).filter(Round.session_id == session_id, Decision.player_type == role, Decision.entity_id == member.entity_id).all())
        logs = db.query(AIUsageLog).filter_by(session_id=session_id, user_id=member.user_id).all()
        rows.append({"user_id": member.user_id, "student": _seat_name(member), "role": role, "entity_id": member.entity_id,
                     "decisions_submitted": sum(item.submission_kind == "human" for item in decisions),
                     "decisions_auto": sum(item.submission_kind != "human" for item in decisions),
                     "ai_prompt_count": len(logs), "ai_total_tokens": sum(item.total_token_count or 0 for item in logs),
                     "ai_rounds_used": len({item.round_number for item in logs}),
                     "login_frequency": None, "login_frequency_note": "Login audit events are not yet collected; this metric is intentionally unavailable."})
    return rows


@router.get("/engagement")
def engagement(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_session_or_404(db, session_id); require_instructor(db, session_id, user.id)
    return {"students": engagement_data(db, session_id)}


@router.get("/decisions")
def decisions(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_session_or_404(db, session_id); require_instructor(db, session_id, user.id)
    grouped = defaultdict(list)
    reviews = db.query(DecisionReview).join(Round).filter(Round.session_id == session_id).order_by(DecisionReview.id).all()
    for review in reviews: grouped[(review.player_type, review.entity_id)].append(review)
    output = []
    for (role, entity_id), records in grouped.items():
        recognized = [int(bool((item.record or {}).get("assessment", {}).get("recognized_constraint"))) for item in records]
        compared = [int(bool((item.record or {}).get("assessment", {}).get("compared_feasible_alternative"))) for item in records]
        output.append({"role": role, "entity_id": entity_id, "submissions_reviewed": len(records),
                       "constraint_recognition_rate": round(sum(recognized) / len(records), 4),
                       "feasible_comparison_rate": round(sum(compared) / len(records), 4),
                       "average_rationale_characters": round(sum(len(str((item.record or {}).get("rationale", ""))) for item in records) / len(records), 2),
                       "trend": "evidence only — instructor interpretation required"})
    return {"decision_quality": sorted(output, key=lambda item: (item["role"], item["entity_id"]))}


@router.get("/balance")
def balance(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = get_session_or_404(db, session_id); require_instructor(db, session_id, user.id)
    nations = [{"nation_id": item.id, "nation": item.name, "gdp": item.gdp, "military_index": item.military_atk + item.military_def + item.military_readiness,
                "market_share": round(sum(company.market_share for company in item.companies), 4)} for item in session.nations]
    nations.sort(key=lambda item: item["gdp"], reverse=True)
    leader = nations[0] if nations else None
    return {"leaderboards": nations, "warnings": ([f"{leader['nation']} leads GDP by more than 25% of the field average"] if leader and leader["gdp"] > (sum(row["gdp"] for row in nations) / len(nations)) * 1.25 else [])}


@router.get("/ai-grading")
def ai_grading(session_id: int, prompt_quality: float = Query(0.45, ge=0), usage_frequency: float = Query(0.25, ge=0), critical_thinking: float = Query(0.30, ge=0), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_session_or_404(db, session_id); require_instructor(db, session_id, user.id)
    rubric = {"prompt_quality": prompt_quality, "usage_frequency": usage_frequency, "critical_thinking": critical_thinking}
    grades = []
    for member in _members(db, session_id):
        logs = db.query(AIUsageLog).filter_by(session_id=session_id, user_id=member.user_id).order_by(AIUsageLog.timestamp).all()
        grades.append({"user_id": member.user_id, "student": _seat_name(member), "role": member.role, "entity_id": member.entity_id, **grade_usage(logs, rubric)})
    return {"grades": grades}


@router.get("/export")
def export(session_id: int, format: str = Query("json", pattern="^(json|csv)$"), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_session_or_404(db, session_id); require_instructor(db, session_id, user.id)
    payload = {"engagement": engagement_data(db, session_id),
               "ai_grading": ai_grading(session_id, prompt_quality=0.45, usage_frequency=0.25, critical_thinking=0.30, db=db, user=user)["grades"],
               "decision_reviews": decisions(session_id, db=db, user=user)["decision_quality"]}
    if format == "json": return payload
    stream = io.StringIO(); writer = csv.DictWriter(stream, fieldnames=["section", "user_id", "student", "role", "entity_id", "data"]); writer.writeheader()
    for section, rows in payload.items():
        for row in rows: writer.writerow({"section": section, "user_id": row.get("user_id", ""), "student": row.get("student", ""), "role": row.get("role", ""), "entity_id": row.get("entity_id", ""), "data": json.dumps(row, sort_keys=True)})
    return Response(stream.getvalue(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=pangeaworld-session-{session_id}-analytics.csv"})
