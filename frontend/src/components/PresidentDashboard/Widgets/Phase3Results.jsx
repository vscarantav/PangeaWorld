import React from 'react';
import { Newspaper } from 'lucide-react';
import { useGame } from '../../../context/GameContext';

const money = (value) => `$${Math.abs(Number(value || 0)).toFixed(2)}M`;

export default function Phase3Results() {
  const { phase3Results, nation } = useGame();
  if (!phase3Results.length) return null;

  return (
    <div className="card col-12">
      <div className="card-header"><h3 className="card-title"><Newspaper /> Pangea Times: Event Results</h3></div>
      <div className="data-list">
        {phase3Results.map((result) => {
          const effect = result.effects || {};
          const affected = result.target_nation_id === nation?.id;
          return <div className="data-item" key={result.event_id} style={{ alignItems: 'flex-start' }}>
            <div className="data-item-info">
              <h4>{result.article?.headline || result.title}</h4>
              <p>{result.article?.summary}</p>
              <p className="text-muted">Round {result.round} · {result.severity === 3 ? 'High' : 'Moderate'} impact</p>
              {affected && <p className="text-muted">Public recovery: {money(effect.public_fund_used)} · Uncovered recovery: {money(effect.private_recovery_total)} · Approval: {Number(effect.approval_delta || 0).toFixed(2)} · GDP: {money(effect.gdp_delta)}</p>}
            </div>
          </div>;
        })}
      </div>
    </div>
  );
}
