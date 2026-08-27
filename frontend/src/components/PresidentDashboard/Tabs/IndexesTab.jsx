import React, { useState } from 'react';
import { LineChart, Gavel, FileText } from 'lucide-react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

export default function IndexesTab({ setBudget }) {
  const [socialBudget, setSocialBudget] = useState(400);
  const [subsidyBudget, setSubsidyBudget] = useState(250);

  const [corpTax, setCorpTax] = useState(21);
  const [incTax, setIncTax] = useState(28);
  const [tariff, setTariff] = useState(15);

  const macroData = {
    labels: ['Round 1', 'Round 2', 'Round 3 (Current)'],
    datasets: [{
      label: 'GDP ($ Trillions)',
      data: [1.10, 1.18, 1.24],
      borderColor: '#10b981',
      backgroundColor: 'rgba(16, 185, 129, 0.2)', // Simplified gradient
      borderWidth: 3,
      fill: true,
      tension: 0.4,
      pointRadius: 4,
      pointBackgroundColor: '#fff'
    }]
  };

  const macroOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        titleColor: '#fff',
        bodyColor: '#10b981',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1
      }
    },
    scales: {
      y: { grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false }, min: 1.0 },
      x: { grid: { display: false } }
    }
  };

  return (
    <section className="dashboard-grid">
      
      <div className="card col-8">
        <div className="card-header">
          <h3 className="card-title"><LineChart /> Macroeconomic Performance</h3>
          <select style={{ background: 'rgba(255,255,255,0.1)', color: 'white', border: 'none', padding: '5px 10px', borderRadius: '4px' }}>
            <option>GDP Growth</option>
            <option>Inflation (CPI)</option>
            <option>Unemployment</option>
          </select>
        </div>
        <div className="chart-container large">
          <Line data={macroData} options={macroOptions} />
        </div>
      </div>

      <div className="card col-4">
        <div className="card-header">
          <h3 className="card-title"><Gavel /> Policy Controls</h3>
        </div>
        <div className="input-group">
          <label>Corporate Tax Rate (%)</label>
          <div className="range-slider-container">
            <input type="range" min="10" max="40" value={corpTax} onChange={e => setCorpTax(Number(e.target.value))} />
            <span className="range-value">{corpTax}%</span>
          </div>
        </div>
        <div className="input-group">
          <label>Income Tax Rate (%)</label>
          <div className="range-slider-container">
            <input type="range" min="10" max="50" value={incTax} onChange={e => setIncTax(Number(e.target.value))} />
            <span className="range-value">{incTax}%</span>
          </div>
        </div>
        <div className="input-group">
          <label>Import Tariffs (Avg %)</label>
          <div className="range-slider-container">
            <input type="range" min="0" max="50" value={tariff} onChange={e => setTariff(Number(e.target.value))} />
            <span className="range-value">{tariff}%</span>
          </div>
        </div>
        <button className="btn" style={{ marginTop: '1rem' }}>Apply Policies</button>
      </div>

      {/* NEW: CPI Breakdown */}
      <div className="card col-4">
        <div className="card-header">
          <h3 className="card-title"><FileText /> CPI Breakdown (Inflation)</h3>
        </div>
        <div className="data-list">
          <div className="data-item">
            <div className="data-item-info">
              <h4>Energy Sector</h4>
            </div>
            <div className="data-item-value text-red">+12.4%</div>
          </div>
          <div className="data-item">
            <div className="data-item-info">
              <h4>Food & Agriculture</h4>
            </div>
            <div className="data-item-value text-yellow">+4.2%</div>
          </div>
          <div className="data-item">
            <div className="data-item-info">
              <h4>Technology</h4>
            </div>
            <div className="data-item-value text-green">-1.5%</div>
          </div>
          <div className="data-item">
            <div className="data-item-info">
              <h4>Labor/Services</h4>
            </div>
            <div className="data-item-value">+2.1%</div>
          </div>
        </div>
      </div>

      <div className="card col-8">
        <div className="card-header">
          <h3 className="card-title">Domestic Budget Allocation (Next Round)</h3>
        </div>
        <div className="dashboard-grid" style={{ gap: '2rem' }}>
          <div className="col-6">
            <div className="input-group">
              <label>Healthcare & Education ($ Millions)</label>
              <div className="range-slider-container">
                <input type="range" min="0" max="1000" value={socialBudget} onChange={e => setSocialBudget(Number(e.target.value))} />
                <span className="range-value">${socialBudget}M</span>
              </div>
            </div>
          </div>
          <div className="col-6">
            <div className="input-group">
              <label>Corporate Subsidies ($ Millions)</label>
              <div className="range-slider-container">
                <input type="range" min="0" max="1000" value={subsidyBudget} onChange={e => setSubsidyBudget(Number(e.target.value))} />
                <span className="range-value">${subsidyBudget}M</span>
              </div>
            </div>
          </div>
        </div>
      </div>

    </section>
  );
}
