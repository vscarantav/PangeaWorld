"""Session-scoped WebSocket notifications; REST remains authoritative."""

from collections import defaultdict
import asyncio

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
        async def send(websocket):
            try:
                await asyncio.wait_for(
                    websocket.send_json({"session_id": session_id, **event}), timeout=1
                )
                return None
            except (RuntimeError, WebSocketDisconnect, OSError, TimeoutError):
                return websocket

        connections = tuple(self.connections.get(session_id, ()))
        if not connections:
            return
        stale = await asyncio.gather(*(send(websocket) for websocket in connections))
        for websocket in stale:
            if websocket is not None:
                self.disconnect(session_id, websocket)


manager = SessionConnectionManager()


def notify_session(session_id: int, event_type: str, **identifiers):
    """Broadcast from a synchronous FastAPI worker after its DB commit."""
    loop = manager.event_loop
    if loop is None or not loop.is_running():
        return
    try:
        asyncio.run_coroutine_threadsafe(
            manager.broadcast(session_id, {"type": event_type, **identifiers}), loop
        )
    except RuntimeError:
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
    try:
        await websocket.send_json({"type": "connected", "session_id": session_id})
    except (RuntimeError, WebSocketDisconnect, OSError):
        manager.disconnect(session_id, websocket)
        return
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(session_id, websocket)
