import React, { useState } from 'react';

export default function DecisionReviewDialog({ request, onClose }) {
  const [alternative, setAlternative] = useState(request.review.alternatives.length ? '' : 'no_feasible_alternative');
  const [rationale, setRationale] = useState('');
  const { review } = request;
  const assumptions = review.assumptions;
  return <div role="dialog" aria-modal="true" aria-label="Compare your decision" style={{ position: 'fixed', inset: 0, zIndex: 2000, background: 'rgba(0,0,0,.85)', overflowY: 'auto', padding: '5vh 10vw' }}>
    <div className="card" style={{ background: '#172235', padding: 24 }}>
      <h2>Compare your decision</h2>
      <p>Constraint: {assumptions.resource}. Available: {assumptions.available.toFixed(2)}.</p>
      <p>Your allocation commits {assumptions.committed.toFixed(2)}, leaving {assumptions.remaining.toFixed(2)}. Recurring wages: {assumptions.recurring_cost.toFixed(2)} per round if hiring is maintained.</p>
      <p>{assumptions.marginal_tradeoff}</p><p>Your projected effects (estimates): {Object.entries(review.selected_projection).map(([key, value]) => `${key.replaceAll("_", " ")}: ${Number(value).toFixed(2)}`).join(" · ")}</p>
      <table><thead><tr><th>Feasible alternative</th><th>Commitment</th><th>Remaining funds</th><th>Projected effects</th></tr></thead><tbody>{review.alternatives.map((item) => <tr key={item.id}><td>{item.label}</td><td>{item.commitment.toFixed(2)}</td><td>{item.remaining.toFixed(2)}</td><td>{Object.entries(item.projection).map(([key, value]) => <p key={key}>{key.replaceAll("_", " ")}: {Number(value).toFixed(2)}</p>)}</td></tr>)}</tbody></table>
      <label>Next-best alternative you are giving up<select aria-label="Foregone alternative" value={alternative} onChange={(event) => setAlternative(event.target.value)}><option value="">Choose an alternative</option>{!review.alternatives.length && <option value="no_feasible_alternative">No different feasible allocation exists</option>}{review.alternatives.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}</select></label>
      <label>Why is your choice preferable? Discuss the next unit of spending and what must wait.<textarea aria-label="Decision rationale" minLength={20} maxLength={2000} value={rationale} onChange={(event) => setRationale(event.target.value)} style={{ width: '100%', minHeight: 100 }} /></label>
      <p>{assumptions.uncertainty}</p>
      <button disabled={!alternative || rationale.trim().length < 20} onClick={() => { request.resolve({ alternative_id: alternative, rationale: rationale.trim(), preview_token: review.preview_token }); onClose(); }}>Confirm reviewed decision</button>
      <button onClick={() => { request.reject(new Error('Submission cancelled. Your draft remains editable.')); onClose(); }}>Cancel</button>
    </div>
  </div>;
}
