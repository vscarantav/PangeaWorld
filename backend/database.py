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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
