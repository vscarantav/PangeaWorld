import React from 'react';
import { useGame } from '../../../context/GameContext';

const money = (value) => `$${Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;

export default function FinancialsTab() {
  const { company, nation, session } = useGame();
  const grossProfit = Math.max(0, Number(company?.revenue || 0) - Number(company?.cogs || 0));
  const history = (session?.rounds || [])
    .filter((round) => round.results?.companies?.some((item) => item.company_id === company?.id))
    .map((round) => round.results.companies.find((item) => item.company_id === company.id));
  const latestResult = history.at(-1);

  return (
    <div className="tab-content">
      <div className="dashboard-grid">
        <div className="card col-12">
          <div className="card-header"><h3 className="card-title"><i className="fa-solid fa-chart-area"></i> Revenue & Net Profit History</h3></div>
          {history.length === 0 ? <p className="text-muted">No completed rounds yet.</p> : (
            <div className="data-list">
              {history.map((item) => <div className="data-item" key={item.company_id + item.revenue}>
                <span>Round {history.indexOf(item) + 1}</span>
                <span className="text-blue">Revenue {money(item.revenue)}</span>
                <span className="positive">Profit {money(item.net_profit)}</span>
              </div>)}
            </div>
          )}
        </div>

        <div className="card col-6">
          <div className="card-header"><h3 className="card-title"><i className="fa-solid fa-file-invoice-dollar"></i> Income Statement</h3></div>
          <div className="data-list">
            <div className="data-item"><span>Gross Revenue</span><span className="data-item-value text-blue">{money(company?.revenue)}</span></div>
            <div className="data-item"><span>Cost of Goods Sold</span><span className="data-item-value text-red">-{money(company?.cogs)}</span></div>
            <div className="data-item"><span>Shipping Costs Recorded</span><span className="data-item-value text-red">-{money(latestResult?.shipping_cost)}</span></div>
            <div className="data-item"><span>Gross Margin</span><span className="data-item-value positive">{Number(company?.gross_margin || 0).toFixed(1)}%</span></div>
          </div>
        </div>

        <div className="card col-6">
          <div className="card-header"><h3 className="card-title"><i className="fa-solid fa-money-bill-wave"></i> Operating Summary</h3></div>
          <div className="data-list">
            <div className="data-item"><span>Gross Profit</span><span className="data-item-value positive">{money(grossProfit)}</span></div>
            <div className="data-item"><span>R&amp;D Investment</span><span className="data-item-value text-red">-{money(latestResult?.rnd_investment)}</span></div>
            <div className="data-item"><span>Corporate Tax Rate</span><span className="data-item-value">{Number((nation?.policies?.tax_rate || 0.15) * 100).toFixed(1)}%</span></div>
            <div className="data-item"><span>Net Profit</span><span className="data-item-value positive">{money(company?.net_profit)}</span></div>
            <div className="data-item"><span>Cash</span><span className="data-item-value text-blue">{money(company?.cash)}</span></div>
          </div>
        </div>
      </div>
    </div>
  );
}
