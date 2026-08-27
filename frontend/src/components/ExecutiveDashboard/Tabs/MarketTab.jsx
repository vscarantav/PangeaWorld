import React from 'react';

export default function MarketTab() {
  return (
    <div className="tab-content">
      <div className="dashboard-grid">
        <div className="card col-12">
          <div className="card-header">
            <h3 className="card-title">
              <i className="fa-solid fa-chart-pie"></i> Global Market Share (Consumer Electronics)
            </h3>
          </div>
          <div className="chart-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px dashed var(--border-light)', borderRadius: '8px' }}>
            <p className="text-muted">Market Share Pie Chart Visualization</p>
          </div>
        </div>

        <div className="card col-6">
          <div className="card-header">
            <h3 className="card-title">
              <i className="fa-solid fa-tags"></i> Competitor Pricing Analysis
            </h3>
          </div>
          <div className="data-list">
            <div className="data-item">
              <div className="data-item-info">
                <h4>Zephyr Ind. (You)</h4>
                <p>Quality: High | Brand: Strong</p>
              </div>
              <span className="data-item-value">$299.00</span>
            </div>
            <div className="data-item">
              <div className="data-item-info">
                <h4>Korvath Tech (User)</h4>
                <p>Quality: Medium | Brand: Average</p>
              </div>
              <span className="data-item-value">$249.00</span>
            </div>
            <div className="data-item">
              <div className="data-item-info">
                <h4>Solhaven Electronics (AI)</h4>
                <p>Quality: Premium | Brand: Luxury</p>
              </div>
              <span className="data-item-value">$499.00</span>
            </div>
            <div className="data-item">
              <div className="data-item-info">
                <h4>Global Average</h4>
              </div>
              <span className="data-item-value text-blue">$349.00</span>
            </div>
          </div>
        </div>

        <div className="card col-6">
          <div className="card-header">
            <h3 className="card-title">
              <i className="fa-solid fa-chart-line"></i> Consumer Demand Curves
            </h3>
          </div>
          <div className="chart-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px dashed var(--border-light)', borderRadius: '8px' }}>
            <p className="text-muted">Price Elasticity vs Demand Chart</p>
          </div>
          <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
            <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}><i className="fa-solid fa-lightbulb text-yellow"></i> Market Insight</h4>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Consumer demand is highly elastic right now due to rising inflation in Terranova. A price cut could capture significant market share from Korvath Tech.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
