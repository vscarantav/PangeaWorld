import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Activity, ArrowRight, BookOpen, ChevronRight, Clock3, Copy, Gamepad2,
  Globe2, GraduationCap, LayoutDashboard, LogOut, Plus, ShieldCheck,
  Sparkles, UserPlus, Users,
} from 'lucide-react';
import * as api from '../../api/client';

const roleLabels = { admin: 'Administrator', professor: 'Professor', student: 'Student' };
const roleIcons = { admin: ShieldCheck, professor: GraduationCap, student: BookOpen };

function Metric({ icon: Icon, label, value, tone = 'blue' }) {
  return <article className={`portal-metric portal-tone-${tone}`}><span><Icon aria-hidden="true" /></span><div><strong>{value}</strong><small>{label}</small></div></article>;
}

function SessionRow({ canAdminOpen, session, onOpen }) {
  const live = session.status === 'active';
  return <div className="portal-session-row">
    <span className={`portal-session-icon ${live ? 'is-live' : ''}`}><Gamepad2 aria-hidden="true" /></span>
    <div className="portal-session-main"><div><strong>Session #{session.id}</strong><span className={`portal-status ${live ? 'is-live' : ''}`}>{live ? 'Live' : session.status}</span></div><p>Round {session.current_round} · {session.phase?.replaceAll('_', ' ')} · {session.member_count} participants</p></div>
    <div className="portal-session-progress"><small>Assigned seats</small><strong>{session.assigned_seats}</strong></div>
    {session.join_code && <button className="portal-code" type="button" title="Copy join code" onClick={() => navigator.clipboard?.writeText(session.join_code)}><Copy aria-hidden="true" />{session.join_code}</button>}
    {(session.is_member || canAdminOpen) && <button className="portal-open" type="button" onClick={() => onOpen(session)}>Open <ChevronRight aria-hidden="true" /></button>}
  </div>;
}

export default function AccountDashboard({
  error, joinCode, onCreateGame, onJoinCodeChange, onJoinGame, onOpenSession,
  onRecoverGame, onSignOut, phaseDurationSeconds, recoverable,
  setPhaseDurationSeconds, user,
}) {
  const [dashboard, setDashboard] = useState(null);
  const [panelError, setPanelError] = useState('');
  const [creatingSession, setCreatingSession] = useState(false);
  const [creatingUser, setCreatingUser] = useState(false);
  const [ownerRole, setOwnerRole] = useState('');
  const [newUser, setNewUser] = useState({ display_name: '', email: '', password: '', account_type: 'student' });
  const loadDashboard = useCallback(() => api.getAccountDashboard().then(setDashboard).catch((err) => setPanelError(err.message)), []);
  useEffect(() => { loadDashboard(); }, [loadDashboard]);

  const accountType = dashboard?.account_type || user.account_type || (user.is_instructor ? 'professor' : 'student');
  const RoleIcon = roleIcons[accountType] || BookOpen;
  const isAdmin = accountType === 'admin';
  const isProfessor = accountType === 'professor';
  const isStaff = isAdmin || isProfessor;
  const sessions = dashboard?.sessions || [];
  const liveSessions = sessions.filter((session) => session.status === 'active').length;
  const counts = dashboard?.counts || {};
  const welcomeName = user.display_name || user.email;
  const metrics = useMemo(() => {
    if (isAdmin) return [
      { icon: Activity, label: 'Live sessions', value: liveSessions, tone: 'green' },
      { icon: Gamepad2, label: 'Total sessions', value: sessions.length },
      { icon: GraduationCap, label: 'Professors', value: counts.professor || 0, tone: 'violet' },
      { icon: Users, label: 'Students', value: counts.student || 0, tone: 'amber' },
    ];
    if (isProfessor) return [
      { icon: Activity, label: 'Live sessions', value: liveSessions, tone: 'green' },
      { icon: Gamepad2, label: 'My sessions', value: sessions.length },
      { icon: Users, label: 'My students', value: dashboard?.users?.length || 0, tone: 'violet' },
    ];
    return [
      { icon: Gamepad2, label: 'My sessions', value: sessions.length },
      { icon: Activity, label: 'Live now', value: liveSessions, tone: 'green' },
    ];
  }, [counts.professor, counts.student, dashboard?.users?.length, isAdmin, isProfessor, liveSessions, sessions.length]);

  const createSession = async () => {
    setCreatingSession(true); setPanelError('');
    try { await onCreateGame(ownerRole || null); } catch (err) { setPanelError(err.message); } finally { setCreatingSession(false); }
  };
  const createUser = async (event) => {
    event.preventDefault(); setCreatingUser(true); setPanelError('');
    try {
      await api.createManagedUser(newUser);
      setNewUser({ display_name: '', email: '', password: '', account_type: 'student' });
      await loadDashboard();
    } catch (err) { setPanelError(err.message); } finally { setCreatingUser(false); }
  };
  const updateRole = async (userId, role) => {
    setPanelError('');
    try { await api.updateAccountRole(userId, role); await loadDashboard(); } catch (err) { setPanelError(err.message); }
  };
  const openSession = async (session) => {
    setPanelError('');
    try {
      if (isAdmin && !session.is_member) await api.claimAdminSessionAccess(session.id);
      await onOpenSession(session.id);
    } catch (err) { setPanelError(err.message); }
  };

  return <main className="account-portal">
    <header className="portal-topbar">
      <div className="portal-logo"><span><Globe2 aria-hidden="true" /></span><strong>Pangea<em>World</em></strong></div>
      <nav className="portal-nav" aria-label="Account dashboard"><span><LayoutDashboard aria-hidden="true" /> Overview</span></nav>
      <div className="portal-profile"><div><strong>{welcomeName}</strong><span><RoleIcon aria-hidden="true" /> {roleLabels[accountType]}</span></div><button type="button" onClick={onSignOut} title="Sign out"><LogOut aria-hidden="true" /></button></div>
    </header>

    <div className="portal-body">
      <section className="portal-welcome">
        <div><span className="portal-eyebrow"><Sparkles aria-hidden="true" /> {roleLabels[accountType]} workspace</span><h1>Welcome, {welcomeName}</h1><p>{isAdmin ? 'Monitor the learning environment, manage access, and follow every live simulation.' : isProfessor ? 'Build your classroom, launch simulations, and guide students through each strategic round.' : 'Join your assigned simulation and focus on the decisions that shape your team’s outcome.'}</p></div>
        <div className="portal-date"><Clock3 aria-hidden="true" /><span>Simulation center<small>Ready for the next round</small></span></div>
      </section>

      <section className="portal-metrics" aria-label="Account overview">{metrics.map((metric) => <Metric key={metric.label} {...metric} />)}</section>
      {(error || panelError) && <div className="portal-alert" role="alert">{panelError || error}</div>}

      <section className={`portal-action-grid ${isStaff ? '' : 'student-layout'}`}>
        {isStaff && <article className="portal-panel portal-create-session">
          <div className="portal-panel-heading"><span><Plus aria-hidden="true" /></span><div><h2>Start a new session</h2><p>Create a fresh seven-round classroom simulation.</p></div></div>
          <div className="portal-session-options"><label className="portal-select-label">Phase deadline<select aria-label="Phase deadline" value={phaseDurationSeconds} onChange={(event) => setPhaseDurationSeconds(Number(event.target.value))}><option value={172800}>48 hours</option><option value={300}>5 minutes (testing)</option><option value={30}>30 seconds (testing)</option><option value={5}>5 seconds (automated testing)</option></select></label><label className="portal-select-label">Your participation<select aria-label="Your participation" value={ownerRole} onChange={(event) => setOwnerRole(event.target.value)}><option value="">Facilitator only</option><option value="president">Play as President</option><option value="executive">Play as Executive</option></select></label></div>
          <button className="portal-primary" aria-label="Create instructor game" type="button" disabled={creatingSession} onClick={createSession}>{creatingSession ? 'Preparing world…' : 'Start new session'}<ArrowRight aria-hidden="true" /></button>
        </article>}

        <article className="portal-panel portal-join-session">
          <div className="portal-panel-heading"><span><Globe2 aria-hidden="true" /></span><div><h2>Join a session</h2><p>Enter the code provided by the session leader.</p></div></div>
          <form onSubmit={(event) => { event.preventDefault(); onJoinGame(); }}><input placeholder="Lobby join code" value={joinCode} onChange={onJoinCodeChange} maxLength={32} /><button type="submit" disabled={!joinCode.trim()}>Join game <ArrowRight aria-hidden="true" /></button></form>
          {!isStaff && <p className="portal-helper"><BookOpen aria-hidden="true" /> Your Professor controls sessions and seat assignments.</p>}
        </article>

        {isStaff && <article className="portal-panel portal-add-person">
          <div className="portal-panel-heading"><span><UserPlus aria-hidden="true" /></span><div><h2>{isAdmin ? 'Add an account' : 'Add a student'}</h2><p>{isAdmin ? 'Create Professor or Student access.' : 'Provision secure access for your class.'}</p></div></div>
          <form className="portal-user-form" onSubmit={createUser}>
            <input aria-label="Display name" placeholder="Full name" value={newUser.display_name} onChange={(event) => setNewUser({ ...newUser, display_name: event.target.value })} required />
            <input aria-label="Account email" type="email" placeholder="Email address" value={newUser.email} onChange={(event) => setNewUser({ ...newUser, email: event.target.value })} required />
            <input aria-label="Temporary password" type="password" minLength={8} placeholder="Temporary password" value={newUser.password} onChange={(event) => setNewUser({ ...newUser, password: event.target.value })} required />
            {isAdmin && <select aria-label="Account type" value={newUser.account_type} onChange={(event) => setNewUser({ ...newUser, account_type: event.target.value })}><option value="student">Student</option><option value="professor">Professor</option></select>}
            <button type="submit" disabled={creatingUser}>{creatingUser ? 'Creating…' : `Add ${isAdmin ? roleLabels[newUser.account_type] : 'Student'}`}<UserPlus aria-hidden="true" /></button>
          </form>
        </article>}
      </section>

      {recoverable.length > 0 && <section className="portal-recovery"><h2>Legacy sessions</h2>{recoverable.map((legacy) => <button key={legacy.id} type="button" onClick={() => onRecoverGame(legacy)}>Recover legacy game #{legacy.id}</button>)}</section>}

      <section className="portal-panel portal-sessions">
        <div className="portal-section-heading"><div><span><Activity aria-hidden="true" /></span><div><h2>{isAdmin ? 'All simulation sessions' : 'My simulation sessions'}</h2><p>{isAdmin ? 'Installation-wide progress and participation.' : 'Resume a lobby or follow current round progress.'}</p></div></div><em>{sessions.length} total</em></div>
        <div className="portal-session-list">{!dashboard ? <p className="portal-empty">Loading sessions…</p> : sessions.length ? sessions.map((session) => <SessionRow canAdminOpen={isAdmin} key={session.id} session={session} onOpen={openSession} />) : <p className="portal-empty">No sessions yet. {isStaff ? 'Start one above when your class is ready.' : 'Join one with your class code.'}</p>}</div>
      </section>

      {isStaff && <section className="portal-panel portal-people">
        <div className="portal-section-heading"><div><span><Users aria-hidden="true" /></span><div><h2>{isAdmin ? 'Account directory' : 'My students'}</h2><p>{isAdmin ? 'Manage installation access levels.' : 'Students provisioned through your workspace.'}</p></div></div><em>{dashboard?.users?.length || 0} accounts</em></div>
        <div className="portal-people-list">{dashboard?.users?.length ? dashboard.users.slice(0, 12).map((person) => <div className="portal-person" key={person.id}><span>{(person.display_name || person.email).slice(0, 1).toUpperCase()}</span><div><strong>{person.display_name || 'Unnamed account'}</strong><small>{person.email}</small></div>{isAdmin ? <select aria-label={`Role for ${person.email}`} value={person.account_type} disabled={person.id === user.id} onChange={(event) => updateRole(person.id, event.target.value)}><option value="admin">Admin</option><option value="professor">Professor</option><option value="student">Student</option></select> : <em>Student</em>}</div>) : <p className="portal-empty">No managed accounts yet.</p>}</div>
      </section>}
    </div>
  </main>;
}
