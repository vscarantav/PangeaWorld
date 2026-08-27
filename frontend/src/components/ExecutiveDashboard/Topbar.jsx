import React from 'react';

export default function Topbar() {
  return (
    <header className="topbar">
      <div className="topbar-title">
        <h1>Executive Dashboard</h1>
      </div>
      
      <div className="kpi-container">
        <div className="kpi">
          <span className="kpi-label">Revenue</span>
          <span className="kpi-value text-blue">$450.2M</span>
        </div>
        <div className="kpi">
          <span className="kpi-label">Net Profit</span>
          <span className="kpi-value positive">+$42.5M</span>
        </div>
        <div className="kpi">
          <span className="kpi-label">Cash Reserves</span>
          <span className="kpi-value positive">$120.0M</span>
        </div>
        <div className="kpi">
          <span className="kpi-label">Market Share</span>
          <span className="kpi-value text-yellow">14.2%</span>
        </div>
      </div>
    </header>
  );
}
