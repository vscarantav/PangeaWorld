"""Shared validation rules for the Phase 3 military/event vertical slice."""

try:
    from ..models.domain import EventType, Nation, Round
except ImportError:
    from models.domain import EventType, Nation, Round


MAX_EVENT_SEVERITY = 3


def validate_event_target(db, round_: Round, event_type: EventType, target_nation_id: int | None):
    """Return the valid target nation or raise without leaking another session."""
    if event_type not in set(EventType):
        raise ValueError("unsupported Phase 3 event type")
    if target_nation_id is None:
        raise ValueError("a natural disaster must target one nation")
    nation = db.query(Nation).filter_by(id=target_nation_id, session_id=round_.session_id).first()
    if nation is None:
        raise ValueError("event target does not belong to this session")
    return nation


def validate_event_severity(severity: int) -> int:
    if isinstance(severity, bool) or not isinstance(severity, int) or not 1 <= severity <= MAX_EVENT_SEVERITY:
        raise ValueError(f"event severity must be an integer from 1 to {MAX_EVENT_SEVERITY}")
    return severity
