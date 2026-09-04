import React from 'react';
import { useGame } from '../../../context/GameContext';

export default function FinancialsTab() {
  const { company } = useGame();
  return (
    <div className="tab-content">
      <div className="dashboard-grid">
        <div className="card col-12">
          <div className="card-header">
            <h3 className="card-title">
              <i className="fa-solid fa-chart-area"></i> Revenue & Net Profit History
            </h3>
          </div>
          <div className="chart-container large" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px dashed var(--border-light)', borderRadius: '8px' }}>
            <p className="text-muted">Interactive Chart Placeholder (Revenue vs Profit)</p>
          </div>
        </div>

        <div className="card col-6">
          <div className="card-header">
            <h3 className="card-title">
              <i className="fa-solid fa-file-invoice-dollar"></i> Income Statement (YTD)
            </h3>
          </div>
          <div className="data-list">
            <div className="data-item">
              <div className="data-item-info">
                <h4>Gross Revenue</h4>
              </div>
                <span className="data-item-value text-blue">${Number(company?.revenue || 0).toLocaleString()}</span>
            </div>
            <div className="data-item">
              <div className="data-item-info">
                <h4>Cost of Goods Sold (COGS)</h4>
                <p>Includes raw materials and production costs</p>
              </div>
              <span className="data-item-value text-red">-${Number(company?.cogs || 0).toLocaleString()}</span>
            </div>
            <div className="data-item">
              <div className="data-item-info">
                <h4>Total Shipping Costs</h4>
                <p>Land, sea, and air freight</p>
              </div>
              <span className="data-item-value text-red">-$52,500,000</span>
            </div>
            <div className="data-item" style={{ borderTop: '1px solid var(--border-light)', marginTop: '0.5rem', paddingTop: '1.5rem' }}>
              <div className="data-item-info">
                <h4>Gross Margin</h4>
              </div>
              <span className="data-item-value positive">{Number(company?.gross_margin || 0).toFixed(1)}%</span>
            </div>
          </div>
        </div>

        <div className="card col-6">
          <div className="card-header">
            <h3 className="card-title">
              <i className="fa-solid fa-money-bill-wave"></i> Operating Expenses & Profit
            </h3>
          </div>
          <div className="data-list">
            <div className="data-item">
              <div className="data-item-info">
                <h4>Gross Profit</h4>
              </div>
              <span className="data-item-value positive">$117,700,000</span>
            </div>
            <div className="data-item">
              <div className="data-item-info">
                <h4>R&D Investment</h4>
              </div>
              <span className="data-item-value text-red">-$25,000,000</span>
            </div>
            <div className="data-item">
              <div className="data-item-info">
                <h4>Corporate Taxes</h4>
                <p>15% Corporate Tax Rate</p>
              </div>
              <span className="data-item-value text-red">-$17,655,000</span>
            </div>
            <div className="data-item">
              <div className="data-item-info">
                <h4>Tariffs Paid</h4>
                <p>Import/Export duties</p>
              </div>
              <span className="data-item-value text-red">-$32,545,000</span>
            </div>
            <div className="data-item" style={{ borderTop: '1px solid var(--border-light)', marginTop: '0.5rem', paddingTop: '1.5rem' }}>
              <div className="data-item-info">
                <h4>Net Profit</h4>
              </div>
              <span className="data-item-value positive">${Number(company?.net_profit || 0).toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
