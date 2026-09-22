import React, { useCallback, useEffect, useState } from 'react';
import { Activity, AlertTriangle, BarChart3, Bot, BrainCircuit, Download, RefreshCw, Scale } from 'lucide-react';
import * as api from '../../api/client';

export default function AnalyticsPanel({ sessionId, phase }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [rubric, setRubric] = useState({ prompt_quality: 0.45, usage_frequency: 0.25, critical_thinking: 0.30 });
  const load = useCallback(async () => {
    setError('');
    try {
      const [engagement, decisions, balance, grading] = await Promise.all([
        api.getAnalyticsEngagement(sessionId), api.getAnalyticsDecisions(sessionId), api.getAnalyticsBalance(sessionId), api.getAnalyticsAiGrading(sessionId, rubric),
      ]);
      setData({ engagement, decisions, balance, grading });
    } catch (err) { setError(err.message); }
  }, [sessionId, rubric]);
  useEffect(() => { load(); }, [load, phase]);

  const sections = data ? [
    { icon: Activity, tone: 'blue', title: 'Engagement', description: 'Participation and AI activity by student', content: <table><thead><tr><th>Student</th><th>Seat</th><th>Human / auto</th><th>AI prompts</th><th>Tokens</th></tr></thead><tbody>{data.engagement.students.map((item) => <tr key={item.user_id}><td><strong>{item.student}</strong></td><td><span className="analytics-seat">{item.role} #{item.entity_id}</span></td><td>{item.decisions_submitted} / {item.decisions_auto}</td><td>{item.ai_prompt_count}</td><td>{item.ai_total_tokens.toLocaleString()}</td></tr>)}</tbody></table> },
    { icon: Bot, tone: 'violet', title: 'AI usage review', description: 'Signals for thoughtful and purposeful tool use', content: <table><thead><tr><th>Student</th><th>Suggested score</th><th>Prompt words</th><th>Topics</th><th>Flags</th></tr></thead><tbody>{data.grading.grades.map((item) => <tr key={item.user_id}><td><strong>{item.student}</strong></td><td><span className="analytics-score">{item.suggested_score}</span><small className="analytics-score-total">/100</small></td><td>{item.average_prompt_words}</td><td>{item.topic_diversity}</td><td>{item.flags.length ? <span className="analytics-flag">{item.flags.join(', ')}</span> : <span className="analytics-clear">Clear</span>}</td></tr>)}</tbody></table> },
    { icon: BrainCircuit, tone: 'green', title: 'Decision-quality evidence', description: 'Observable reasoning behaviors from submissions', content: <table><thead><tr><th>Seat</th><th>Reviews</th><th>Constraints</th><th>Alternatives</th><th>Rationale length</th></tr></thead><tbody>{data.decisions.decision_quality.map((item) => <tr key={`${item.role}-${item.entity_id}`}><td><strong className="instructor-capitalize">{item.role} #{item.entity_id}</strong></td><td>{item.submissions_reviewed}</td><td>{Math.round(item.constraint_recognition_rate * 100)}%</td><td>{Math.round(item.feasible_comparison_rate * 100)}%</td><td>{item.average_rationale_characters} chars</td></tr>)}</tbody></table> },
    { icon: Scale, tone: 'amber', title: 'Game balance', description: 'Comparative nation performance this round', content: <table><thead><tr><th>Nation</th><th>GDP</th><th>Military index</th><th>Market share</th></tr></thead><tbody>{data.balance.leaderboards.map((item, index) => <tr key={item.nation_id}><td><span className="analytics-rank">{index + 1}</span><strong>{item.nation}</strong></td><td>{item.gdp.toLocaleString(undefined, { maximumFractionDigits: 1 })}</td><td>{item.military_index.toFixed(1)}</td><td>{item.market_share.toFixed(1)}%</td></tr>)}</tbody></table> },
  ] : [];

  return <details className="instructor-panel analytics-panel" open><summary><span className="instructor-summary-icon"><BarChart3 aria-hidden="true" /></span><span><small>Learning intelligence</small><strong>Phase 4 instructor analytics</strong></span><em>Live evidence</em></summary>
    <div className="instructor-panel-body">
      <div className="analytics-intro"><div><h2>Evidence at a glance</h2><p>Use these signals to support your review—not as automatic grades of student reasoning.</p></div><div className="analytics-actions">
        <button onClick={load} aria-label="Refresh analytics"><RefreshCw aria-hidden="true" /> Refresh</button><a href={api.analyticsExportUrl(sessionId, 'json')} target="_blank" rel="noreferrer"><Download aria-hidden="true" /> JSON</a><a href={api.analyticsExportUrl(sessionId, 'csv')} target="_blank" rel="noreferrer"><Download aria-hidden="true" /> CSV</a>
      </div></div>
      <fieldset className="analytics-rubric"><legend>AI-usage rubric</legend><div className="analytics-rubric-grid">{Object.entries(rubric).map(([key, value]) => <label key={key}><span>{key.replaceAll('_', ' ')}</span><span className="analytics-weight"><input aria-label={`${key.replaceAll('_', ' ')} weight`} type="number" min="0" step="0.05" value={value} onChange={(event) => setRubric((current) => ({ ...current, [key]: Math.max(0, Number(event.target.value) || 0) }))} /><em>{Math.round(value * 100)}%</em></span></label>)}</div><small>Weights are normalized automatically when analytics refresh.</small></fieldset>
      {error && <p className="instructor-alert" role="alert"><AlertTriangle aria-hidden="true" />{error}</p>}
      {!data && !error && <div className="instructor-loading"><span /><p>Gathering classroom analytics…</p></div>}
      {data && <div className="analytics-sections">{sections.map(({ icon: Icon, tone, title, description, content }) => <section className="analytics-section" key={title}><header><span className={`analytics-section-icon is-${tone}`}><Icon aria-hidden="true" /></span><div><h3>{title}</h3><p>{description}</p></div></header><div className="analytics-table-wrap">{content}</div></section>)}{data.balance.warnings.map((warning) => <p className="analytics-warning" key={warning}><AlertTriangle aria-hidden="true" />{warning}</p>)}</div>}
    </div>
  </details>;
}
