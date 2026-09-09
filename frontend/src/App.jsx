import React, { useEffect, useState } from 'react';
import PresidentDashboard from './components/PresidentDashboard';
import ExecutiveDashboard from './components/ExecutiveDashboard';
import GameMap from './components/GameMap';
import './index.css';
import { GameProvider, useGame } from './context/GameContext';
import * as api from './api/client';
import { generateMapData } from './utils/MapGenerator';

function serializeStartingMap(map, seed) {
  return {
    seed,
    triangles: map.triangles.map((triangle) => ({ id: triangle.id, terrain: triangle.terrain.name, points: triangle.points })),
    edges: map.edges.map((edge) => ({ id: edge.id, triangle_ids: edge.triangles.map((triangle) => triangle.id), has_railroad: Boolean(edge.hasRailroad), is_river: Boolean(edge.isRiver), is_impassable: Boolean(edge.isImpassable) })),
    countries: map.countries.map((country) => ({ id: country.id, name: country.name, x: country.x, y: country.y, labelX: country.labelX, labelY: country.labelY })),
    cities: map.triangles.filter((triangle) => triangle.isSmallCity || triangle.isBigCity).map((triangle) => ({ id: triangle.id, triangle_id: triangle.id, country_id: triangle.country?.id, is_port: Boolean(triangle.isPort), is_big_city: Boolean(triangle.isBigCity) })),
  };
}

function GameShell() {
  const { loading, error, session, nation, company, membership } = useGame();

  const [role, setRole] = useState(membership?.role === 'president' ? 'president' : 'executive');
  const [readiness, setReadiness] = useState(null);
  useEffect(() => { if (!session?.id) return undefined; const load = () => api.getReadiness(session.id).then(setReadiness).catch(() => {}); load(); const timer = window.setInterval(load, 15000); return () => window.clearInterval(timer); }, [session?.id]);

  if (loading) return <div style={{ padding: '3rem', color: 'white' }}>Connecting to PangeaWorld server…</div>;
  if (error) return <div style={{ padding: '3rem', color: '#f87171' }}>Unable to connect to the game server: {error}</div>;
  return (
    <>
      <div style={{ position: 'fixed', top: '10px', left: '50%', transform: 'translateX(-50%)', zIndex: 9999, background: 'rgba(0,0,0,0.8)', padding: '5px 10px', borderRadius: '20px', border: '1px solid var(--border-light)', display: 'flex', gap: '10px', alignItems: 'center' }}>
        <span style={{ color: 'white', padding: '5px 15px', fontWeight: 'bold' }}>{membership?.role === 'president' ? 'President' : 'Company Executive'}</span>
        <button 
          onClick={() => setRole(role === 'map' ? membership?.role === 'president' ? 'president' : 'executive' : 'map')}
          style={{ background: role === 'map' ? 'var(--accent-primary)' : 'transparent', color: 'white', border: 'none', padding: '5px 15px', borderRadius: '15px', cursor: 'pointer', fontWeight: 'bold' }}
        >
          {role === 'map' ? 'Return to dashboard' : 'Map View'}
        </button>
        
      </div>
      
        <div style={{ position: 'fixed', bottom: 16, left: 16, zIndex: 9999, background: 'rgba(15,23,42,.95)', padding: '10px 14px', borderRadius: 8, color: 'white', border: '1px solid var(--border-light)' }}>
          Round {session.current_round} · {session.phase} · {nation?.name || 'No nation'} · {company?.name || 'No company'}
          {readiness?.my_status && ` · Decision: ${readiness.my_status}`}
        </div>
      {role === 'president' && <PresidentDashboard />}
      {role === 'executive' && <ExecutiveDashboard />}
      {role === 'map' && (
          <div style={{ width: '100vw', height: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center', backgroundColor: '#1e1e1e' }}>
              <GameMap seed={session.seed} mapSnapshot={session.map_snapshot} isPlanningMode={false} />
          </div>
      )}
    </>
  );
}

function AuthAndLobby() {
  const [user, setUser] = useState(null); const [email, setEmail] = useState(''); const [password, setPassword] = useState('');
  const [joinCode, setJoinCode] = useState(''); const [lobby, setLobby] = useState(null); const [error, setError] = useState('');
  const [registering, setRegistering] = useState(false);
  const loadLobby = async (id) => { const next = await api.getLobby(id); setLobby(next); window.localStorage.setItem('pangeaworld.sessionId', id); };
  useEffect(() => { api.getMe().then(({ user: current }) => { setUser(current); const id = window.localStorage.getItem('pangeaworld.sessionId'); if (id) loadLobby(id).catch(() => window.localStorage.removeItem('pangeaworld.sessionId')); }).catch(() => {}); }, []);
  useEffect(() => {
    if (!lobby || lobby.status !== 'lobby') return undefined;
    const timer = window.setInterval(() => api.getLobby(lobby.session_id).then(setLobby).catch(() => {}), 10000);
    return () => window.clearInterval(timer);
  }, [lobby?.session_id, lobby?.status]);
  const authenticate = async (event) => { event.preventDefault(); setError(''); try { const result = registering ? await api.register({ email, password }) : await api.login({ email, password }); setUser(result.user); } catch (err) { setError(err.message); } };
  const createGame = async () => { try { const game = await api.createSession(); await api.updateMap(game.id, serializeStartingMap(generateMapData(game.seed), game.seed)); await loadLobby(game.id); } catch (err) { setError(err.message); } };
  const joinGame = async () => { try { const result = await api.joinLobby(joinCode); await loadLobby(result.session_id); } catch (err) { setError(err.message); } };
  if (!user) return <main className="auth-page"><h1>PangeaWorld</h1><form onSubmit={authenticate}><input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} /><input type="password" placeholder="Password (8+ characters)" value={password} onChange={e => setPassword(e.target.value)} /><button>{registering ? 'Create account' : 'Sign in'}</button></form><button onClick={() => setRegistering(!registering)}>{registering ? 'Already have an account?' : 'Need an account?'}</button>{error && <p>{error}</p>}</main>;
  if (!lobby) return <main className="auth-page"><h1>Welcome, {user.display_name || user.email}</h1>{user.is_instructor && <button onClick={createGame}>Create instructor game</button>}<div><input placeholder="Lobby join code" value={joinCode} onChange={e => setJoinCode(e.target.value)} /><button onClick={joinGame}>Join game</button></div>{!user.is_instructor && <p>Ask your instructor for a lobby join code.</p>}{error && <p>{error}</p>}</main>;
  const mine = lobby.my_membership;
  if (lobby.status === 'lobby') return <main className="auth-page"><h1>Game lobby</h1>{mine.role === 'instructor' ? <InstructorLobby lobby={lobby} refresh={() => loadLobby(lobby.session_id)} /> : <p>{mine.entity_id ? `Assigned as ${mine.role}. Waiting for the instructor to start the game.` : 'Waiting for the instructor to assign your seat.'}</p>}<button onClick={() => { api.logout(); setUser(null); setLobby(null); }}>Sign out</button></main>;
  if (mine.role === 'instructor') return <InstructorGame sessionId={lobby.session_id} />;
  if (!mine.entity_id) return <main className="auth-page">This game has started, but you do not have an assigned seat.</main>;
  return <GameProvider sessionId={lobby.session_id} membership={mine}><GameShell /></GameProvider>;
}

function InstructorLobby({ lobby, refresh }) {
  const [error, setError] = useState('');
  const assign = async (userId, role, entityId) => { try { await api.assignSeat(lobby.session_id, { user_id: userId, role, entity_id: Number(entityId) }); refresh(); } catch (err) { setError(err.message); } };
  return <><p>Share join code: <strong>{lobby.join_code}</strong></p><p>{lobby.members.length} players in lobby</p><p>{lobby.seats.nations.filter(s => !s.occupied).length} president seats and {lobby.seats.companies.filter(s => !s.occupied).length} executive seats available; unfilled seats will be AI-vacant.</p>{lobby.members.filter(m => m.role !== 'instructor').map(member => <div key={member.id}><span>{member.display_name} — {member.role}{member.entity_id ? ` #${member.entity_id}` : ''}</span><select defaultValue="" onChange={e => { const [role, id] = e.target.value.split(':'); if (id) assign(member.user_id, role, id); }}><option value="">Assign seat…</option><optgroup label="Presidents">{lobby.seats.nations.map(s => <option key={`p${s.id}`} disabled={s.occupied} value={`president:${s.id}`}>{s.name}{s.occupied ? ' (occupied)' : ''}</option>)}</optgroup><optgroup label="Executives">{lobby.seats.companies.map(s => <option key={`e${s.id}`} disabled={s.occupied} value={`executive:${s.id}`}>{s.name}{s.occupied ? ' (occupied)' : ''}</option>)}</optgroup></select></div>)}<button onClick={() => api.startLobby(lobby.session_id).then(refresh).catch(e => setError(e.message))}>Start game</button>{error && <p>{error}</p>}</>;
}

function InstructorGame({ sessionId }) {
  const [summary, setSummary] = useState(null); const [error, setError] = useState('');
  const refresh = () => api.getReadiness(sessionId).then(setSummary).catch(err => setError(err.message));
  useEffect(() => { refresh(); const timer = window.setInterval(refresh, 15000); return () => window.clearInterval(timer); }, [sessionId]);
  const advance = async () => { try { await api.advanceRound(sessionId); await refresh(); } catch (err) { setError(err.message); } };
  return <main className="auth-page"><h1>Instructor readiness board</h1>{summary && <><p>Round {summary.round} · {summary.phase}</p><p>{summary.submitted}/{summary.total} assigned seats submitted.</p>{summary.seats.map(seat => <p key={`${seat.role}-${seat.entity_id}`}>{seat.role} #{seat.entity_id}: {seat.status}</p>)}</>}{error && <p>{error}</p>}<button onClick={refresh}>Refresh</button><button onClick={advance}>Advance phase</button></main>;
}

function App() {
  return <AuthAndLobby />;
}

export default App;
