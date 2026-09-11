# pyrefly: ignore [missing-import]
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

try:
    from .database import engine, Base, get_db, ensure_schema
    from .models.domain import GameSession, PhaseEnum
    from .seed_data import seed_game_session
    from .routes.sessions import router as sessions_router
    from .routes.nations import router as nations_router
    from .routes.companies import router as companies_router
    from .routes.decisions import router as decisions_router
    from .routes.market import router as market_router
    from .routes.auth import router as auth_router
    from .routes.phase3 import router as phase3_router
    from .routes.advisor import router as advisor_router
    from .routes.ai_logs import router as ai_logs_router
    from .realtime import router as realtime_router
except ImportError:  # Allows `uvicorn main:app` from inside backend.
    from database import engine, Base, get_db, ensure_schema
    from models.domain import GameSession, PhaseEnum
    from seed_data import seed_game_session
    from routes.sessions import router as sessions_router
    from routes.nations import router as nations_router
    from routes.companies import router as companies_router
    from routes.decisions import router as decisions_router
    from routes.market import router as market_router
    from routes.auth import router as auth_router
    from routes.phase3 import router as phase3_router
    from routes.advisor import router as advisor_router
    from routes.ai_logs import router as ai_logs_router
    from realtime import router as realtime_router

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Prepare the local schema and seed the development session once."""
    Base.metadata.create_all(bind=engine)
    ensure_schema()
    db = next(get_db())
    try:
        default_session = db.query(GameSession).first()
        if not default_session:
            default_session = GameSession(seed="default_dev_seed", phase=PhaseEnum.PLANNING)
            db.add(default_session)
            db.commit()
            db.refresh(default_session)
            seed_game_session(db, default_session.id)
        yield
    finally:
        db.close()


app = FastAPI(title="PangeaWorld API", lifespan=lifespan)
app.include_router(sessions_router)
app.include_router(nations_router)
app.include_router(companies_router)
app.include_router(decisions_router)
app.include_router(market_router)
app.include_router(auth_router)
app.include_router(phase3_router)
app.include_router(advisor_router)
app.include_router(ai_logs_router)
app.include_router(realtime_router)

# Configure CORS so the React frontend can communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "online", "message": "PangeaWorld Game Server is running."}
