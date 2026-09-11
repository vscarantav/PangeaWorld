"""Deterministic control state for seats without an assigned human."""


def is_scripted_seat(session, nation) -> bool:
    return session.ruleset_version == "phase3-closure-v1" and nation.archetype == "Marginalized military state"


def human_controlled_seats(session):
    return {(member.role, member.entity_id) for member in session.memberships if member.entity_id is not None}


def is_backfilled(session, role: str, entity_id: int) -> bool:
    """A non-scripted seat is AI-controlled unless a membership owns it."""
    return (role, entity_id) not in human_controlled_seats(session)
