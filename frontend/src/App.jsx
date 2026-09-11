import InstructorPhase3 from './components/InstructorPhase3';
import AnalyticsPanel from './components/InstructorDashboard/AnalyticsPanel';
import BackfillPanel from './components/InstructorDashboard/BackfillPanel';
import DebriefPanel from './components/Debrief/DebriefPanel';
import DecisionFeedback from './components/DecisionFeedback';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import PresidentDashboard from './components/PresidentDashboard';
import ExecutiveDashboard from './components/ExecutiveDashboard';
import GameMap from './components/GameMap';
import './index.css';
import { GameProvider, useGame } from './context/GameContext';
import * as api from './api/client';
import { generateMapData } from './utils/MapGenerator';
import { serializeMapSnapshot } from './utils/MapSnapshot';
import { useSessionEvents } from './hooks/useSessionEvents';

function DeadlineCountdown({ deadlineAt, serverTime }) {
  const [remaining, setRemaining] = useState(null);
  useEffect(() => {
    if (!deadlineAt || !serverTime) return undefined;
    const serverOffset = Date.parse(serverTime) - Date.now();
    const update = () => setRemaining(Math.max(0, Date.parse(deadlineAt) - (Date.now() + serverOffset)));
    update();
    const timer = window.setInterval(update, 1000);
    return () => window.clearInterval(timer);
  }, [deadlineAt, serverTime]);
  if (!deadlineAt || !serverTime || remaining === null) return null;
  const totalSeconds = Math.ceil(remaining / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return <span> · Deadline: {hours}h {minutes}m {seconds}s</span>;
}

function decisionStatusLabel(status) {
  return status === 'auto_submitted' ? 'automatic (deadline missed)' : status?.replaceAll('_', ' ');
}

function isOlderLobbyStatus(current, incoming) {
  const rank = { lobby: 0, active: 1, complete: 2 };
  return current?.session_id === incoming?.session_id
    && (rank[incoming.status] ?? -1) < (rank[current.status] ?? -1);
}

async function getCurrentUserWithRetry() {
  let latestError;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      return await api.getMe();
    } catch (error) {
      latestError = error;
      const transient = /did not respond|failed to fetch|network/i.test(error.message);
      if (!transient || attempt === 2) throw error;
      await new Promise((resolve) => window.setTimeout(resolve, 250 * (attempt + 1)));
    }
  }
  throw latestError;
}

function GameShell({ onSignOut }) {
  const { loading, error, session, nation, company, membership, news, readiness, realtimeConnected, refresh, loadMapSnapshot } = useGame();
  const dashboardRole = membership?.role === 'president' ? 'president' : 'executive';
  const [view, setView] = useState(dashboardRole);

  useEffect(() => {
    if (!session?.id) return undefined;
    const load = () => refresh(session.id).catch(() => {});
    const timer = window.setInterval(load, 15000);
    return () => window.clearInterval(timer);
  }, [session?.id, refresh]);

  if (loading) return <div style={{ padding: '3rem', color: 'white' }}>Connecting to PangeaWorld server…</div>;
  if (error && !session) return <div style={{ padding: '3rem', color: '#f87171' }}>Unable to connect to the game server: {error}</div>;
  if (!session) return <div style={{ padding: '3rem', color: 'white' }}>Connecting to PangeaWorld server…</div>;
  const latestCompletedRound = [...(session.rounds || [])].reverse().find((round) => round.status === 'complete' && round.results?.nations);
  return (
    <>
      <div style={{ position: 'fixed', top: 10, left: '50%', transform: 'translateX(-50%)', zIndex: 9999, background: 'rgba(0,0,0,0.8)', padding: '5px 10px', borderRadius: 20, border: '1px solid var(--border-light)', display: 'flex', gap: 10, alignItems: 'center' }}>
        <span style={{ color: 'white', padding: '5px 15px', fontWeight: 'bold' }}>{dashboardRole === 'president' ? 'President' : 'Company Executive'}</span>
        <button
          onClick={async () => {
            if (view === 'map') {
              setView(dashboardRole);
              return;
            }
            if (!session.map_snapshot) await loadMapSnapshot();
            setView('map');
          }}
          style={{ background: view === 'map' ? 'var(--accent-primary)' : 'transparent', color: 'white', border: 'none', padding: '5px 15px', borderRadius: 15, cursor: 'pointer', fontWeight: 'bold' }}
        >
          {view === 'map' ? 'Return to dashboard' : 'Map View'}
        </button>
        <button onClick={onSignOut}>Sign out</button>
      </div>
      <div data-testid="game-status" style={{ position: 'fixed', bottom: 16, left: 16, zIndex: 9999, background: 'rgba(15,23,42,.95)', padding: '10px 14px', borderRadius: 8, color: 'white', border: '1px solid var(--border-light)' }}>
        Round {session.current_round} · {session.phase} · {nation?.name || 'No nation'} · {company?.name || 'No company'}
        {readiness?.my_status && ` · Decision: ${decisionStatusLabel(readiness.my_status)}`}
        {` · ${realtimeConnected ? 'Live' : 'Reconnecting…'}`}
        <DeadlineCountdown deadlineAt={readiness?.deadline_at} serverTime={readiness?.server_time} />
      </div>
      {latestCompletedRound && <aside data-testid="round-results" style={{ position: 'fixed', bottom: 16, right: 16, zIndex: 9999, maxWidth: 360, background: 'rgba(15,23,42,.96)', padding: '12px 16px', borderRadius: 8, color: 'white', border: '1px solid var(--border-light)' }}><strong>Round {latestCompletedRound.number} results published</strong><p style={{ margin: '6px 0 0' }}>Pangea Times: {news[0]?.headline || 'Round results are available.'}</p></aside>}
      {session.phase === 'complete' && <DebriefPanel sessionId={session.id} />}
      {view === 'president' && (nation ? <PresidentDashboard /> : <div style={{ padding: '3rem', color: 'white' }}>Loading nation dashboard…</div>)}
      {view === 'executive' && (company ? <ExecutiveDashboard /> : <div style={{ padding: '3rem', color: 'white' }}>Loading company dashboard…</div>)}
      {view === 'map' && (
        <div style={{ width: '100vw', height: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center', backgroundColor: '#1e1e1e' }}>
          <GameMap seed={session.seed} mapSnapshot={session.map_snapshot} isPlanningMode={false} />
        </div>
      )}
    </>
  );
}

function AuthAndLobby() {
  const [user, setUser] = useState(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [joinCode, setJoinCode] = useState('');
  const [lobby, setLobby] = useState(null);
  const [recoverable, setRecoverable] = useState([]);
  const [error, setError] = useState('');
  const [registering, setRegistering] = useState(false);
  const [loadingAuth, setLoadingAuth] = useState(true);
  const [phaseDurationSeconds, setPhaseDurationSeconds] = useState(172800);
  const lobbyRequestInFlight = useRef(null);

  const applyLobby = useCallback((next) => {
    setLobby((current) => isOlderLobbyStatus(current, next) ? current : next);
  }, []);

  const loadLobby = useCallback(async (id) => {
    const requestId = String(id);
    if (lobbyRequestInFlight.current?.id === requestId) return lobbyRequestInFlight.current.promise;
    const request = (async () => {
      const next = await api.getLobby(id);
      applyLobby(next);
      window.localStorage.setItem('pangeaworld.sessionId', id);
      return next;
    })();
    lobbyRequestInFlight.current = { id: requestId, promise: request };
    try {
      return await request;
    } finally {
      if (lobbyRequestInFlight.current?.promise === request) lobbyRequestInFlight.current = null;
    }
  }, [applyLobby]);

  const loadRecoverable = useCallback(async (currentUser) => {
    if (!currentUser?.is_instructor) return;
    setRecoverable(await api.getRecoverableSessions());
  }, []);

  const restoreLobby = useCallback(async () => {
    const id = window.localStorage.getItem('pangeaworld.sessionId');
    if (!id) return false;
    try {
      await loadLobby(id);
      return true;
    } catch {
      window.localStorage.removeItem('pangeaworld.sessionId');
      return false;
    }
  }, [loadLobby]);

  useEffect(() => {
    let active = true;
    getCurrentUserWithRetry()
      .then(async ({ user: current }) => {
        if (!active) return;
        setUser(current);
        const restored = await restoreLobby();
        if (!restored && active) await loadRecoverable(current);
      })
      .catch(() => {})
      .finally(() => { if (active) setLoadingAuth(false); });
    return () => { active = false; };
  }, [loadRecoverable, restoreLobby]);

  useEffect(() => {
    const sessionId = lobby?.session_id;
    if (!sessionId || lobby.status !== 'lobby') return undefined;
    // WebSocket is the fast path. A short REST fallback prevents a player from
    // remaining in the lobby when the game-start event lands during reconnect.
    const timer = window.setInterval(() => api.getLobby(sessionId).then(applyLobby).catch(() => {}), 3000);
    return () => window.clearInterval(timer);
  }, [lobby?.session_id, lobby?.status, applyLobby]);

  const lobbyRealtimeConnected = useSessionEvents(lobby?.status === 'lobby' ? lobby.session_id : null, () => {
    if (lobby?.session_id) loadLobby(lobby.session_id).catch(() => {});
  });

  const authenticate = async (event) => {
    event.preventDefault();
    setError('');
    try {
      const result = registering ? await api.register({ email, password }) : await api.login({ email, password });
      setUser(result.user);
      const restored = await restoreLobby();
      if (!restored) await loadRecoverable(result.user);
    } catch (err) {
      setError(err.message);
    }
  };

  const signOut = async () => {
    setError('');
    try {
      await api.logout();
    } catch (err) {
      setError(err.message);
    } finally {
      setUser(null);
      setLobby(null);
      setRecoverable([]);
      setRegistering(false);
    }
  };

  const createGame = async () => {
    setError('');
    try {
      const game = await api.createSession(phaseDurationSeconds);
      await generateAndPersistMap(game.id, game.seed);
      await loadLobby(game.id);
    } catch (err) {
      setError(err.message);
    }
  };

  const recoverGame = async (legacy) => {
    setError('');
    try {
      const result = await api.claimLegacySession(legacy.id);
      await loadLobby(result.session.id);
      if (result.requires_map_rebuild) {
        await generateAndPersistMap(result.session.id, result.session.seed);
        await loadLobby(result.session.id);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const generateAndPersistMap = async (sessionId, seed) => {
    const snapshot = serializeMapSnapshot(generateMapData(seed), seed);
    return api.updateMap(sessionId, snapshot);
  };

  const joinGame = async () => {
    setError('');
    try {
      const result = await api.joinLobby(joinCode);
      await loadLobby(result.session_id);
    } catch (err) {
      setError(err.message);
    }
  };

  if (loadingAuth) return <main className="auth-page"><h1>PangeaWorld</h1><p>Restoring your secure session…</p></main>;
  if (!user) return <main className="auth-page"><h1>PangeaWorld</h1><form onSubmit={authenticate}><input placeholder="Email" value={email} onChange={(event) => setEmail(event.target.value)} /><input type="password" placeholder="Password (8+ characters)" value={password} onChange={(event) => setPassword(event.target.value)} /><button>{registering ? 'Create account' : 'Sign in'}</button></form><button onClick={() => setRegistering(!registering)}>{registering ? 'Already have an account?' : 'Need an account?'}</button>{error && <p>{error}</p>}</main>;
  if (!lobby) return <main className="auth-page"><h1>Welcome, {user.display_name || user.email}</h1>{user.is_instructor && <div><label>Phase deadline <select aria-label="Phase deadline" value={phaseDurationSeconds} onChange={(event) => setPhaseDurationSeconds(Number(event.target.value))}><option value={172800}>48 hours</option><option value={300}>5 minutes (testing)</option><option value={30}>30 seconds (testing)</option><option value={5}>5 seconds (automated testing)</option></select></label><button onClick={createGame}>Create instructor game</button></div>}{recoverable.map((legacy) => <button key={legacy.id} onClick={() => recoverGame(legacy)}>Recover legacy game #{legacy.id}</button>)}<div><input placeholder="Lobby join code" value={joinCode} onChange={(event) => setJoinCode(event.target.value)} /><button onClick={joinGame}>Join game</button></div>{!user.is_instructor && <p>Ask your instructor for a lobby join code.</p>}<button onClick={signOut}>Sign out</button>{error && <p>{error}</p>}</main>;

  const mine = lobby.my_membership;
  if (lobby.status === 'lobby') return <main className="auth-page"><h1>Game lobby</h1><p data-testid="lobby-connection">{lobbyRealtimeConnected ? 'Live' : 'Reconnecting…'}</p>{mine.role === 'instructor' ? <InstructorLobby lobby={lobby} refresh={() => loadLobby(lobby.session_id)} generateMap={() => generateAndPersistMap(lobby.session_id, lobby.seed).then(() => loadLobby(lobby.session_id))} /> : <PlayerLobby lobby={lobby} refresh={() => loadLobby(lobby.session_id)} />}<button onClick={signOut}>Sign out</button></main>;
  if (mine.role === 'instructor') return <InstructorGame sessionId={lobby.session_id} onSignOut={signOut} />;
  if (!mine.entity_id) return <main className="auth-page"><p>This game has started, but you do not have an assigned seat.</p><button onClick={signOut}>Sign out</button></main>;
  return <GameProvider sessionId={lobby.session_id} membership={mine}><GameShell onSignOut={signOut} /></GameProvider>;
}

function PlayerLobby({ lobby, refresh }) {
  const [name, setName] = useState('');
  const [message, setMessage] = useState('');
  const membership = lobby.my_membership;
  const rename = async () => {
    try {
      if (membership.role === 'president') await api.renameNation(lobby.session_id, membership.entity_id, name);
      if (membership.role === 'executive') await api.renameCompany(lobby.session_id, membership.entity_id, name);
      setMessage('Name updated.');
      setName('');
      await refresh();
    } catch (error) {
      setMessage(error.message);
    }
  };
  return <>{membership.entity_id ? <><p>Assigned as {membership.role}. Waiting for the instructor to start the game.</p><div><input maxLength={60} placeholder={`Rename your ${membership.role === 'president' ? 'nation' : 'company'}`} value={name} onChange={(event) => setName(event.target.value)} /><button disabled={name.trim().length < 2} onClick={rename}>Update name</button></div>{message && <p>{message}</p>}</> : <p>Waiting for the instructor to assign your seat.</p>}</>;
}

function InstructorLobby({ lobby, refresh, generateMap }) {
  const [error, setError] = useState('');
  const assign = async (userId, role, entityId) => {
    try {
      await api.assignSeat(lobby.session_id, { user_id: userId, role, entity_id: Number(entityId) });
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  };
  return <><p>Share join code: <strong>{lobby.join_code}</strong></p><p>{lobby.members.length} players in lobby</p><p>{lobby.seats.nations.filter((seat) => !seat.occupied).length} president seats and {lobby.seats.companies.filter((seat) => !seat.occupied).length} executive seats available; unfilled seats will be AI-vacant.</p>{!lobby.has_map_snapshot && <button onClick={() => generateMap().catch((mapError) => setError(mapError.message))}>Generate starting map</button>}{lobby.members.filter((member) => member.role !== 'instructor').map((member) => <div key={member.id} data-member-email={member.display_name}><span>{member.display_name} — {member.role}{member.entity_id ? ` #${member.entity_id}` : ''}</span><select defaultValue="" onChange={(event) => { const [role, id] = event.target.value.split(':'); if (id) assign(member.user_id, role, id); }}><option value="">Assign seat…</option><optgroup label="Presidents">{lobby.seats.nations.map((seat) => <option key={`p${seat.id}`} disabled={seat.occupied} value={`president:${seat.id}`}>{seat.name}{seat.occupied ? ' (occupied)' : ''}</option>)}</optgroup><optgroup label="Executives">{lobby.seats.companies.map((seat) => <option key={`e${seat.id}`} disabled={seat.occupied} value={`executive:${seat.id}`}>{seat.name}{seat.occupied ? ' (occupied)' : ''}</option>)}</optgroup></select></div>)}<button disabled={!lobby.has_map_snapshot} onClick={() => api.startLobby(lobby.session_id).then(refresh).catch((error) => setError(error.message))}>Start game</button>{error && <p>{error}</p>}</>;
}

function InstructorGame({ sessionId, onSignOut }) {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState('');
  const refreshing = useRef(false);
  const refresh = useCallback(async () => {
    if (refreshing.current) return;
    refreshing.current = true;
    try {
      setSummary(await api.getReadiness(sessionId));
      setError('');
    } catch (err) {
      setError(err.message);
    } finally {
      refreshing.current = false;
    }
  }, [sessionId]);
  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 5000);
    return () => window.clearInterval(timer);
  }, [refresh]);
  const realtimeConnected = useSessionEvents(sessionId, refresh);
  const advance = async () => {
    try {
      await api.advanceRound(sessionId, summary.phase);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  };
  return <main className="auth-page"><h1>Instructor readiness board</h1><InstructorPhase3 sessionId={sessionId} phase={summary?.phase} /><AnalyticsPanel sessionId={sessionId} phase={summary?.phase} /><BackfillPanel sessionId={sessionId} phase={summary?.phase} /><DecisionFeedback sessionId={sessionId} round={summary?.round} />{summary?.phase === 'complete' && <DebriefPanel sessionId={sessionId} />}<p>{realtimeConnected ? 'Live' : 'Reconnecting…'}</p>{summary && <><p>Round {summary.round} · {summary.phase}<DeadlineCountdown deadlineAt={summary.deadline_at} serverTime={summary.server_time} /></p><p>{summary.submitted}/{summary.total} assigned seats submitted.</p>{summary.seats.map((seat) => <p key={`${seat.role}-${seat.entity_id}`}>{seat.role} #{seat.entity_id}: {decisionStatusLabel(seat.status)}</p>)}</>}{error && <p>{error}</p>}<button onClick={refresh}>Refresh</button><button disabled={!summary || summary.phase === 'complete'} onClick={advance}>Advance phase</button><button onClick={onSignOut}>Sign out</button></main>;
}

export default function App() {
  return <AuthAndLobby />;
}
