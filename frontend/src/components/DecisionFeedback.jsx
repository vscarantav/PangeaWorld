import React, { useEffect, useState } from 'react';
import { getDecisionReviews } from '../api/client';

export default function DecisionFeedback({ sessionId, round }) {
  const [reviews, setReviews] = useState([]);
  const [reports, setReports] = useState([]);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    getDecisionReviews(sessionId).then((data) => { if (active) { setReviews(data.reviews); setReports(data.intelligence_reports || []); } }).catch((err) => { if (active) setError(err.message); });
    return () => { active = false; };
  }, [sessionId, round]);
  return <details className="card" style={{ margin: 20, padding: 20 }}><summary>Decision reasoning and round feedback</summary>{error && <p>{error}</p>}{!reviews.length && <p>Reviewed submissions will appear here.</p>}{reviews.map((item) => <article key={item.id}>
    <h4>Round {item.round} · {item.player_type} #{item.entity_id} · submission {item.id}{item.superseded ? " (superseded before resolution)" : ""}</h4>
    <p>Foregone alternative: {item.record.foregone.label}. Rationale: {item.record.rationale}</p>
    <p>Committed {item.record.assumptions.committed.toFixed(2)} from {item.record.assumptions.available.toFixed(2)} available.</p>
    {item.feedback && <><p>{item.feedback.comparison}</p><p>Alternative funds remaining minus selected funds remaining: {item.feedback.resource_remaining_difference_at_submission.toFixed(2)}.</p><p>Realized funds: {Number(item.feedback.realized.treasury ?? item.feedback.realized.cash ?? 0).toFixed(2)} · {item.feedback.realized.gdp != null ? `GDP: ${item.feedback.realized.gdp.toFixed(2)}` : `Profit: ${Number(item.feedback.realized.net_profit || 0).toFixed(2)}`}</p></>}
    <p>Assessment evidence: constraint recognized; {item.record.assessment.compared_feasible_alternative ? "feasible alternative compared" : "no different feasible allocation available"}; rationale recorded. Reasoning quality requires instructor review.</p>
  </article>)}{reports.map((report) => <p key={report.id}>Private intelligence · nation {report.target_id} · round {report.observed_round}: readiness {report.readiness}, posture {report.posture}. {report.limitation}</p>)}</details>;
}
