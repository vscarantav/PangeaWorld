from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from models.domain import Company, GameSession, MapSnapshot, Nation, PhaseEnum, Round, RoundStatus
from seed_data import NATIONS_DATA, seed_game_session


def make_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_seed_creates_complete_day1_foundation():
    db = make_db()
    session = GameSession(seed="test-seed", phase=PhaseEnum.PLANNING)
    db.add(session)
    db.commit()

    seed_game_session(db, session.id)

    assert db.query(Nation).filter_by(session_id=session.id).count() == 8
    assert db.query(Company).join(Nation).filter(Nation.session_id == session.id).count() == 80
    assert db.query(Round).filter_by(session_id=session.id).one().status == RoundStatus.PLANNING
    assert {nation.name for nation in db.query(Nation).all()} == {
        nation["name"] for nation in NATIONS_DATA
    }


def test_map_snapshot_is_session_scoped_and_persistable():
    db = make_db()
    session = GameSession(seed="map-seed")
    db.add(session)
    db.commit()

    snapshot = MapSnapshot(
        session_id=session.id,
        validated_map_json={"seed": "map-seed", "validated": True},
    )
    db.add(snapshot)
    db.commit()
    db.refresh(session)

    assert session.map_snapshots[0].validated_map_json["validated"] is True
