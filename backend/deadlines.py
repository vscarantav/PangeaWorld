"""Timezone-safe helpers for authoritative multiplayer phase deadlines."""

from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock


_session_mutation_locks = defaultdict(Lock)


def session_mutation_lock(session_id: int) -> Lock:
    """Serialize deadline-sensitive writes in local/SQLite deployments."""
    return _session_mutation_locks[session_id]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def active_deadline(session) -> datetime | None:
    if session.phase.value == "presidential":
        return as_utc(session.presidential_deadline_at)
    if session.phase.value == "company":
        return as_utc(session.company_deadline_at)
    return None


def deadline_has_passed(session, now: datetime | None = None) -> bool:
    deadline = active_deadline(session)
    return deadline is not None and deadline <= (now or utc_now())
