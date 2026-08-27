import React, { useState } from 'react';
import { Landmark, Globe } from 'lucide-react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function FinancingTab({ setBudget }) {
  const [debtBudget, setDebtBudget] = useState(150);
  const [quotaBudget, setQuotaBudget] = useState(50);

  const debtData = {
    labels: ['R1', 'R2', 'R3', 'R4 (Proj)', 'R5 (Proj)'],
    datasets: [
      {
        label: 'FMI Loans',
        data: [200, 350, 450, 400, 300],
        backgroundColor: '#ef4444',
        stack: 'Stack 0',
      },
      {
        label: 'National Treasury',
        data: [800, 750, 600, 650, 800],
        backgroundColor: '#3b82f6',
        stack: 'Stack 0',
      }
    ]
  };

  const debtOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: '#f8fafc' } }
    },
    scales: {
      y: { 
        stacked: true, 
        grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false },
        title: { display: true, text: 'Millions ($)', color: '#94a3b8' }
      },
      x: { 
        stacked: true,
        grid: { display: false }
      }
    }
  };

  return (
    <section className="dashboard-grid">
      <div className="card col-6">
        <div className="card-header">
          <h3 className="card-title"><Landmark /> Treasury & Debt Profile</h3>
        </div>
        <div className="chart-container">
          <Bar data={debtData} options={debtOptions} />
        </div>
      </div>
      
      <div className="card col-6">
        <div className="card-header">
          <h3 className="card-title"><Globe /> FMI Portal</h3>
          <span className="text-green">Credit Rating: AA-</span>
        </div>
        <div className="data-list">
          <div className="data-item">
            <div className="data-item-info">
              <h4>Active Loan: Dev. Package 2028</h4>
              <p>Interest: 4.5% | Maturing: Round 6</p>
            </div>
            <div className="data-item-value text-red">-$450M</div>
          </div>
          <div className="data-item">
            <div className="data-item-info">
              <h4>FMI Quota Contribution</h4>
              <p>Increases national borrowing limit</p>
            </div>
            <div className="data-item-value text-blue">+$100M</div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
          <button className="btn secondary">Request New Loan</button>
          <button className="btn">Increase FMI Quota</button>
        </div>
      </div>
      
      <div className="card col-12">
        <div className="card-header">
          <h3 className="card-title">Financial Budget Allocation (Next Round)</h3>
        </div>
        <div className="dashboard-grid" style={{ gap: '2rem' }}>
          <div className="col-6">
            <div className="input-group">
              <label>FMI Debt Repayment ($ Millions)</label>
              <div className="range-slider-container">
                <input type="range" min="0" max="1000" value={debtBudget} onChange={e => setDebtBudget(Number(e.target.value))} />
                <span className="range-value">${debtBudget}M</span>
              </div>
            </div>
          </div>
          <div className="col-6">
            <div className="input-group">
              <label>FMI Quota Increase ($ Millions)</label>
              <div className="range-slider-container">
                <input type="range" min="0" max="1000" value={quotaBudget} onChange={e => setQuotaBudget(Number(e.target.value))} />
                <span className="range-value">${quotaBudget}M</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
