import React from 'react';
import { useGame } from '../../context/GameContext';

export default function Topbar() {
  const { company, session } = useGame();
  return (
    <header className="topbar">
      <div className="topbar-title">
        <h1>Executive Dashboard <span style={{ color: 'var(--text-muted)', fontSize: '1rem', fontWeight: 'normal' }}>· Round {session?.current_round}</span></h1>
      </div>
      
      <div className="kpi-container">
        <div className="kpi">
          <span className="kpi-label">Revenue</span>
          <span className="kpi-value text-blue">${Number(company?.revenue || 0).toLocaleString()}</span>
        </div>
        <div className="kpi">
          <span className="kpi-label">Net Profit</span>
          <span className="kpi-value positive">+${Number(company?.net_profit || 0).toLocaleString()}</span>
        </div>
        <div className="kpi">
          <span className="kpi-label">Cash Reserves</span>
          <span className="kpi-value positive">${Number(company?.cash || 0).toLocaleString()}</span>
        </div>
        <div className="kpi">
          <span className="kpi-label">Market Share</span>
          <span className="kpi-value text-yellow">{Number(company?.market_share || 0).toFixed(1)}%</span>
        </div>
      </div>
    </header>
  );
}
