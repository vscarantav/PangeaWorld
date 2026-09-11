import React, { useCallback, useEffect, useState } from 'react';
import * as api from '../../api/client';

export default function AnalyticsPanel({ sessionId, phase }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const load = useCallback(async () => {
    setError('');
    try {
      const [engagement, decisions, balance, grading] = await Promise.all([
        api.getAnalyticsEngagement(sessionId), api.getAnalyticsDecisions(sessionId), api.getAnalyticsBalance(sessionId), api.getAnalyticsAiGrading(sessionId),
      ]);
      setData({ engagement, decisions, balance, grading });
    } catch (err) { setError(err.message); }
  }, [sessionId]);
  useEffect(() => { load(); }, [load, phase]);
  return <details open><summary>Phase 4 instructor analytics</summary>
    <p>These scores are evidence for review, not automatic grades of student reasoning.</p>
    <button onClick={load}>Refresh analytics</button>{' '}
    <a href={api.analyticsExportUrl(sessionId, 'json')} target="_blank" rel="noreferrer">Export JSON</a>{' · '}
    <a href={api.analyticsExportUrl(sessionId, 'csv')} target="_blank" rel="noreferrer">Export CSV</a>
    {error && <p role="alert">{error}</p>}
    {!data && !error && <p>Loading analytics…</p>}
    {data && <>
      <h3>Engagement</h3><table><thead><tr><th>Student</th><th>Seat</th><th>Human / auto decisions</th><th>AI prompts</th><th>Tokens</th></tr></thead><tbody>{data.engagement.students.map((item) => <tr key={item.user_id}><td>{item.student}</td><td>{item.role} #{item.entity_id}</td><td>{item.decisions_submitted} / {item.decisions_auto}</td><td>{item.ai_prompt_count}</td><td>{item.ai_total_tokens}</td></tr>)}</tbody></table>
      <h3>AI usage review</h3><table><thead><tr><th>Student</th><th>Suggested score</th><th>Prompt words</th><th>Topics</th><th>Flags</th></tr></thead><tbody>{data.grading.grades.map((item) => <tr key={item.user_id}><td>{item.student}</td><td>{item.suggested_score}/100</td><td>{item.average_prompt_words}</td><td>{item.topic_diversity}</td><td>{item.flags.join(', ') || 'None'}</td></tr>)}</tbody></table>
      <h3>Decision-quality evidence</h3><table><thead><tr><th>Seat</th><th>Reviews</th><th>Constraints recognized</th><th>Alternatives compared</th><th>Rationale length</th></tr></thead><tbody>{data.decisions.decision_quality.map((item) => <tr key={`${item.role}-${item.entity_id}`}><td>{item.role} #{item.entity_id}</td><td>{item.submissions_reviewed}</td><td>{Math.round(item.constraint_recognition_rate * 100)}%</td><td>{Math.round(item.feasible_comparison_rate * 100)}%</td><td>{item.average_rationale_characters}</td></tr>)}</tbody></table>
      <h3>Game balance</h3><table><thead><tr><th>Nation</th><th>GDP</th><th>Military index</th><th>Market share</th></tr></thead><tbody>{data.balance.leaderboards.map((item) => <tr key={item.nation_id}><td>{item.nation}</td><td>{item.gdp.toFixed(1)}</td><td>{item.military_index.toFixed(1)}</td><td>{item.market_share.toFixed(1)}</td></tr>)}</tbody></table>
      {data.balance.warnings.map((warning) => <p key={warning}>{warning}</p>)}
    </>}
  </details>;
}
