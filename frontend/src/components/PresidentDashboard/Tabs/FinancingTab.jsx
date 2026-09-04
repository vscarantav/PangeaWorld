import React from 'react';
import { Landmark, Globe } from 'lucide-react';
import { useGame } from '../../../context/GameContext';

export default function FinancingTab() {
  const { nation, session } = useGame();
  const history = (session?.rounds || []).filter((round) => round.results?.nations?.some((item) => item.nation_id === nation?.id));
  return (
    <section className="dashboard-grid">
      <div className="card col-6"><div className="card-header"><h3 className="card-title"><Landmark /> Treasury History</h3></div>
        <div className="data-list">
          <div className="data-item"><span>Current Treasury</span><span className="data-item-value text-blue">${Number(nation?.treasury || 0).toLocaleString()}M</span></div>
          {history.map((round) => <div className="data-item" key={round.number}><span>After Round {round.number}</span><span className="data-item-value">${Number(round.results.nations.find((item) => item.nation_id === nation.id)?.treasury || 0).toLocaleString()}M</span></div>)}
        </div>
      </div>
      <div className="card col-6"><div className="card-header"><h3 className="card-title"><Globe /> FMI Portal</h3></div>
        <p className="text-muted">Debt and FMI lending mechanics are not enabled in the Phase 1 engine yet.</p>
      </div>
      <div className="card col-12"><div className="card-header"><h3 className="card-title">Available Financial Data</h3></div>
        <div className="data-list"><div className="data-item"><span>Trade Balance</span><span className="data-item-value">${Number(nation?.trade_balance || 0).toLocaleString()}M</span></div><div className="data-item"><span>Tax Rate</span><span className="data-item-value">{Number((nation?.policies?.tax_rate || 0) * 100).toFixed(1)}%</span></div><div className="data-item"><span>Tariff Rate</span><span className="data-item-value">{Number((nation?.policies?.tariffs || 0) * 100).toFixed(1)}%</span></div></div>
      </div>
    </section>
  );
}
