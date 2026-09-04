import React from 'react';
import { useGame } from '../../../context/GameContext';

const money = (value) => `$${Number(value || 0).toFixed(2)}`;

export default function MarketTab() {
  const { market, company, companies } = useGame();
  const widgetPrice = company?.products?.Widget?.price || 0;
  const pricedCompanies = (companies || []).filter((item) => item.products?.Widget?.price != null);
  const averagePrice = pricedCompanies.length ? pricedCompanies.reduce((sum, item) => sum + Number(item.products.Widget.price), 0) / pricedCompanies.length : 0;

  return (
    <div className="tab-content">
      <div className="dashboard-grid">
        <div className="card col-12">
          <div className="card-header"><h3 className="card-title"><i className="fa-solid fa-chart-pie"></i> Global Market Share</h3></div>
          {pricedCompanies.length === 0 ? <p className="text-muted">No company market data is available.</p> : (
            <div className="data-list">{pricedCompanies.slice(0, 10).map((item) => <div className="data-item" key={item.id}>
              <span>{item.name}{item.id === company?.id ? ' (You)' : ''}</span>
              <span className="data-item-value text-yellow">{Number(item.market_share || 0).toFixed(1)}%</span>
            </div>)}</div>
          )}
        </div>

        <div className="card col-6">
          <div className="card-header"><h3 className="card-title"><i className="fa-solid fa-tags"></i> Product Pricing</h3></div>
          <div className="data-list">
            <div className="data-item"><span>Your Widget price</span><span className="data-item-value">{money(widgetPrice)}</span></div>
            <div className="data-item"><span>Global Widget average</span><span className="data-item-value text-blue">{money(averagePrice)}</span></div>
            <div className="data-item"><span>Companies reporting a price</span><span className="data-item-value">{pricedCompanies.length}</span></div>
          </div>
        </div>

        <div className="card col-6">
          <div className="card-header"><h3 className="card-title"><i className="fa-solid fa-chart-line"></i> Resource Market</h3></div>
          <div className="data-list">{Object.entries(market?.resources || {}).map(([resource, data]) => <div className="data-item" key={resource}>
            <span>{resource}</span><span className="data-item-value">{Number(data.global_stockpile || 0).toFixed(1)} available · {money(data.current_price ?? data.base_price)}</span>
          </div>)}</div>
        </div>
      </div>
    </div>
  );
}
