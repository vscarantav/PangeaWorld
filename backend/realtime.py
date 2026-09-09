"""Session-scoped WebSocket notifications; REST remains authoritative."""

from collections import defaultdict
import asyncio
from concurrent.futures import TimeoutError as FutureTimeoutError

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

try:
    from .auth import SESSION_COOKIE, _as_utc, _token_hash, _utc_now
    from .database import get_db
    from .models.domain import AuthSession, GameMembership
except ImportError:
    from auth import SESSION_COOKIE, _as_utc, _token_hash, _utc_now
    from database import get_db
    from models.domain import AuthSession, GameMembership


router = APIRouter(tags=["realtime"])


class SessionConnectionManager:
    def __init__(self):
        self.connections = defaultdict(set)
        self.event_loop = None

    async def connect(self, session_id: int, websocket: WebSocket):
        self.event_loop = asyncio.get_running_loop()
        await websocket.accept()
        self.connections[session_id].add(websocket)

    def disconnect(self, session_id: int, websocket: WebSocket):
        self.connections[session_id].discard(websocket)
        if not self.connections[session_id]:
            self.connections.pop(session_id, None)

    async def broadcast(self, session_id: int, event: dict):
        stale = []
        for websocket in tuple(self.connections.get(session_id, ())):
            try:
                await websocket.send_json({"session_id": session_id, **event})
            except (RuntimeError, WebSocketDisconnect, OSError):
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(session_id, websocket)


manager = SessionConnectionManager()


def notify_session(session_id: int, event_type: str, **identifiers):
    """Broadcast from a synchronous FastAPI worker after its DB commit."""
    loop = manager.event_loop
    if loop is None or not loop.is_running():
        return
    try:
        future = asyncio.run_coroutine_threadsafe(
            manager.broadcast(session_id, {"type": event_type, **identifiers}), loop
        )
        future.result(timeout=5)
    except (RuntimeError, FutureTimeoutError):
        # A closing development server may tear down its loop during a request.
        return


@router.websocket("/api/sessions/{session_id}/ws")
async def session_websocket(websocket: WebSocket, session_id: int, db: Session = Depends(get_db)):
    raw_token = websocket.cookies.get(SESSION_COOKIE)
    auth_session = db.query(AuthSession).filter_by(
        token_hash=_token_hash(raw_token or ""), revoked_at=None
    ).first()
    if auth_session is None or _as_utc(auth_session.expires_at) <= _utc_now():
        await websocket.close(code=4401)
        return
    membership = db.query(GameMembership).filter_by(session_id=session_id, user_id=auth_session.user_id).first()
    if membership is None:
        await websocket.close(code=4403)
        return
    # The socket can live for hours, but its authentication transaction should
    # not. In particular, an open SQLite read transaction can block game writes.
    db.close()
    await manager.connect(session_id, websocket)
    await websocket.send_json({"type": "connected", "session_id": session_id})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(session_id, websocket)
