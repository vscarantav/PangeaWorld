import React, { useEffect, useState } from 'react';
import * as api from '../api/client';

export default function InstructorPhase3({ sessionId, phase }) {
  const [nations, setNations] = useState([]);
  const [target, setTarget] = useState('');
  const [mode, setMode] = useState('scripted');
  const [category, setCategory] = useState('natural_disaster');
  const [title, setTitle] = useState('Regional recovery challenge');
  const [summary, setSummary] = useState('An instructor-authored disruption challenges national preparedness.');
  const [severity, setSeverity] = useState(2);
  const [cpi, setCpi] = useState(0);
  const [approval, setApproval] = useState(0);
  const [message, setMessage] = useState('');
  const [scorecards, setScorecards] = useState([]);
  useEffect(() => {
    let active = true;
    Promise.all([api.getNations(sessionId), api.getPhase3Settings(sessionId), api.getOpportunityCostScorecard(sessionId)]).then(([rows, settings, scorecard]) => {
      if (active) { setNations(rows); setMode(settings.drakmoor_mode); setScorecards(scorecard.scorecards); }
    }).catch((error) => { if (active) setMessage(error.message); });
    return () => { active = false; };
  }, [sessionId, phase]);
  const saveBehavior = async () => { try { await api.savePhase3Settings(sessionId, mode); setMessage('Drakmoor behavior recorded.'); } catch (err) { setMessage(err.message); } };
  const inject = async () => { try { await api.injectScenario(sessionId, { catalog_key: 'custom', target_nation_id: Number(target), scenario: { title, summary, event_type: category, severity, cpi_delta: cpi, approval_delta: approval } }); setMessage('Scenario scheduled for the active round.'); } catch (err) { setMessage(err.message); } };
  return <details><summary>Phase 3 instructor controls</summary>
    <label>Drakmoor behavior<select value={mode} onChange={(e) => setMode(e.target.value)}><option value="scripted">Scripted: reconnaissance in year 1, attacks from year 2</option><option value="passive">Passive</option></select></label><button disabled={phase !== 'planning'} onClick={saveBehavior}>Save behavior</button>
    <p>One injected scenario per active round. Natural disasters use severity-based recovery; other categories apply the bounded CPI and approval changes below.</p>
    <label>Target<select value={target} onChange={(e) => setTarget(e.target.value)}><option value="">Choose nation</option>{nations.map((nation) => <option key={nation.id} value={nation.id}>{nation.name}</option>)}</select></label>
    <label>Category<select value={category} onChange={(e) => setCategory(e.target.value)}>{['natural_disaster','political_crisis','market_shock','health_emergency','technology_breakthrough'].map((value) => <option key={value}>{value}</option>)}</select></label>
    <label>Title<input value={title} maxLength={120} onChange={(e) => setTitle(e.target.value)} /></label><label>Scenario description<textarea value={summary} maxLength={500} onChange={(e) => setSummary(e.target.value)} /></label>
    <label>Severity<input type="number" min="1" max="3" value={severity} onChange={(e) => setSeverity(Number(e.target.value))} /></label>
    <label>CPI change<input disabled={category === 'natural_disaster'} type="number" min="-5" max="10" value={cpi} onChange={(e) => setCpi(Number(e.target.value))} /></label><label>Approval change<input disabled={category === 'natural_disaster'} type="number" min="-10" max="10" value={approval} onChange={(e) => setApproval(Number(e.target.value))} /></label>
    <button disabled={!target || !['planning','presidential','company'].includes(phase)} onClick={inject}>Schedule scenario</button>{message && <p>{message}</p>}
    <h3>Opportunity-cost scorecard</h3>
    {!scorecards.length && <p>No reviewed submissions yet.</p>}
    {scorecards.length > 0 && <table><thead><tr><th>Seat</th><th>Reviewed</th><th>Constraints</th><th>Alternatives</th><th>Revisions</th></tr></thead><tbody>{scorecards.map((item) => <tr key={`${item.player_type}-${item.entity_id}`}><td>{item.player_type} #{item.entity_id}</td><td>{item.submissions_reviewed}</td><td>{Math.round(item.constraint_recognition_rate * 100)}%</td><td>{Math.round(item.feasible_comparison_rate * 100)}%</td><td>{item.revision_count}</td></tr>)}</tbody></table>}
    <p>These are evidence counts for instructor review, not automatic grades of reasoning quality.</p>
  </details>;
}
