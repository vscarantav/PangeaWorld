import React from 'react';
import SupplyChainMap from '../Widgets/SupplyChainMap';

export default function SourcingTab() {
  return (
    <div className="tab-content">
      <div className="dashboard-grid">
        <div className="card col-8">
          <div className="card-header">
            <h3 className="card-title">
              <i className="fa-solid fa-map-location-dot"></i> Global Supply Chain
            </h3>
          </div>
          <SupplyChainMap />
        </div>

        <div className="card col-4">
          <div className="card-header">
            <h3 className="card-title">
              <i className="fa-solid fa-boxes-stacked"></i> Supplier Marketplace
            </h3>
          </div>
          <div className="input-group">
            <label>Required Resource</label>
            <select style={{ width: '100%', padding: '0.75rem', background: 'rgba(255,255,255,0.1)', border: '1px solid var(--border-light)', color: 'white', borderRadius: '8px' }}>
              <option>Steel (Korvath)</option>
              <option>Oil (Valdoria)</option>
              <option>Timber (Nordvik)</option>
              <option>Grain (Terranova)</option>
            </select>
          </div>
          
          <div className="data-list" style={{ marginTop: '1rem' }}>
            <div className="data-item" style={{ cursor: 'pointer', border: '1px solid var(--accent-primary)' }}>
              <div className="data-item-info">
                <h4>Korvath Steel Co. (User)</h4>
                <p>Base: $50/unit | Transit: 1 Round</p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span className="data-item-value">$62 landed</span>
                <p style={{ fontSize: '0.7rem', color: 'var(--accent-primary)' }}>Via Rail</p>
              </div>
            </div>
            <div className="data-item" style={{ cursor: 'pointer' }}>
              <div className="data-item-info">
                <h4>Drakmoor Forge (AI)</h4>
                <p>Base: $30/unit | Transit: 2 Rounds</p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span className="data-item-value text-red">Sanctioned</span>
                <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Trade Blocked</p>
              </div>
            </div>
            <div className="data-item" style={{ cursor: 'pointer' }}>
              <div className="data-item-info">
                <h4>Valdorian Metals (AI)</h4>
                <p>Base: $55/unit | Transit: 1 Round</p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span className="data-item-value">$59 landed</span>
                <p style={{ fontSize: '0.7rem', color: 'var(--accent-secondary)' }}>Via Sea</p>
              </div>
            </div>
          </div>
        </div>

        <div className="card col-12">
          <div className="card-header">
            <h3 className="card-title">
              <i className="fa-solid fa-truck-fast"></i> Logistics Breakdown
            </h3>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-light)', textAlign: 'left', color: 'var(--text-muted)' }}>
                <th style={{ padding: '1rem' }}>Supplier</th>
                <th style={{ padding: '1rem' }}>Mode</th>
                <th style={{ padding: '1rem' }}>Base Price</th>
                <th style={{ padding: '1rem' }}>Shipping Cost</th>
                <th style={{ padding: '1rem' }}>Tariffs</th>
                <th style={{ padding: '1rem' }}>Total Landed Cost</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '1rem' }}>Valdorian Metals</td>
                <td style={{ padding: '1rem' }}><i className="fa-solid fa-ship text-blue"></i> Sea</td>
                <td style={{ padding: '1rem' }}>$55.00</td>
                <td style={{ padding: '1rem' }}>$2.00</td>
                <td style={{ padding: '1rem' }}>$2.00</td>
                <td style={{ padding: '1rem', fontWeight: 'bold' }}>$59.00</td>
              </tr>
              <tr>
                <td style={{ padding: '1rem' }}>Korvath Steel Co.</td>
                <td style={{ padding: '1rem' }}><i className="fa-solid fa-train text-yellow"></i> Rail</td>
                <td style={{ padding: '1rem' }}>$50.00</td>
                <td style={{ padding: '1rem' }}>$12.00</td>
                <td style={{ padding: '1rem' }}>$0.00 (FTA)</td>
                <td style={{ padding: '1rem', fontWeight: 'bold' }}>$62.00</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
