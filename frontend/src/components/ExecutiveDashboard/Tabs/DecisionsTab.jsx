import React from 'react';
import NewsFeed from '../Widgets/NewsFeed';

export default function DecisionsTab() {
  return (
    <div className="tab-content">
      <div className="dashboard-grid">
        <div className="card col-8">
          <div className="card-header">
            <h3 className="card-title">
              <i className="fa-solid fa-gavel"></i> Round 3 Decisions
            </h3>
            <span style={{ fontSize: '0.8rem', background: 'rgba(59, 130, 246, 0.2)', color: 'var(--accent-primary)', padding: '0.25rem 0.75rem', borderRadius: '12px' }}>
              Phase 2: Company Phase
            </span>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {/* Sales & Pricing */}
            <div style={{ padding: '1.5rem', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', border: '1px solid var(--border-light)' }}>
              <h4 style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between' }}>
                <span>1. Product Pricing</span>
                <span className="text-muted" style={{ fontWeight: 'normal', fontSize: '0.9rem' }}>Current: $299.00</span>
              </h4>
              <div className="input-group">
                <label>Set Retail Price</label>
                <div className="range-slider-container">
                  <span className="text-muted">$150</span>
                  <input type="range" min="150" max="600" defaultValue="299" />
                  <span className="range-value">$299</span>
                </div>
              </div>
            </div>

            {/* Production */}
            <div style={{ padding: '1.5rem', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', border: '1px solid var(--border-light)' }}>
              <h4 style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between' }}>
                <span>2. Production Volume</span>
                <span className="text-muted" style={{ fontWeight: 'normal', fontSize: '0.9rem' }}>Current Capacity: 1.5M units</span>
              </h4>
              <div className="input-group">
                <label>Target Production Units</label>
                <div className="range-slider-container">
                  <span className="text-muted">0M</span>
                  <input type="range" min="0" max="1500000" step="50000" defaultValue="1200000" />
                  <span className="range-value">1.2M</span>
                </div>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Estimated COGS for this volume: $280M</p>
            </div>

            {/* R&D */}
            <div style={{ padding: '1.5rem', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', border: '1px solid var(--border-light)' }}>
              <h4 style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between' }}>
                <span>3. R&D Investment</span>
                <span className="text-muted" style={{ fontWeight: 'normal', fontSize: '0.9rem' }}>Improves product quality</span>
              </h4>
              <div className="input-group">
                <label>Budget Allocation</label>
                <div className="range-slider-container">
                  <span className="text-muted">$0M</span>
                  <input type="range" min="0" max="100000000" step="1000000" defaultValue="25000000" />
                  <span className="range-value">$25M</span>
                </div>
              </div>
            </div>

            <button className="btn" style={{ marginTop: '1rem', padding: '1rem', fontSize: '1.1rem' }}>
              <i className="fa-solid fa-lock"></i> Lock In Decisions
            </button>
          </div>
        </div>

        <div className="card col-4">
          <NewsFeed />
        </div>
      </div>
    </div>
  );
}
