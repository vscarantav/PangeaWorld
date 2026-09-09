from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_PATH = Path(__file__).resolve().with_name("pangeaworld.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

# Setting check_same_thread=False is needed for SQLite when used with FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_schema():
    """Apply the small, backwards-compatible SQLite additions used locally.

    SQLAlchemy's ``create_all`` does not alter an existing development database.
    Keeping this migration here prevents an existing local game from breaking
    when round result history is added.
    """
    Base.metadata.create_all(bind=engine)
    columns = {column["name"] for column in inspect(engine).get_columns("rounds")}
    if "results" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE rounds ADD COLUMN results JSON"))
    nation_columns = {column["name"] for column in inspect(engine).get_columns("nations")}
    if "approval_rating" not in nation_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE nations ADD COLUMN approval_rating FLOAT DEFAULT 60.0"))
    session_columns = {column["name"] for column in inspect(engine).get_columns("game_sessions")}
    with engine.begin() as connection:
        if "lobby_join_code" not in session_columns:
            connection.execute(text("ALTER TABLE game_sessions ADD COLUMN lobby_join_code VARCHAR"))
        if "lobby_code_revoked" not in session_columns:
            connection.execute(text("ALTER TABLE game_sessions ADD COLUMN lobby_code_revoked INTEGER DEFAULT 0"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_game_sessions_lobby_join_code ON game_sessions (lobby_join_code)"))
    user_columns = {column["name"] for column in inspect(engine).get_columns("users")}
    if "is_instructor" not in user_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN is_instructor INTEGER DEFAULT 0"))
    # Preserve local Day 1 installations: when accounts predate the instructor
    # flag, promote the earliest account once so it can recover old sessions.
    with engine.begin() as connection:
        has_instructor = connection.execute(text("SELECT 1 FROM users WHERE is_instructor = 1 LIMIT 1")).first()
        if has_instructor is None:
            connection.execute(text("UPDATE users SET is_instructor = 1 WHERE id = (SELECT MIN(id) FROM users)"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
