import React, { useState } from 'react';
import { Target, UserCheck, Skull, Expand, MapPin } from 'lucide-react';
import { Chart as ChartJS, RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend } from 'chart.js';
import { Radar } from 'react-chartjs-2';

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

export default function IntelTab({ setBudget, onOpenProjectModal }) {
  const [troopBudget, setTroopBudget] = useState(300);
  const [intelBudget, setIntelBudget] = useState(150);
  const [covertBudget, setCovertBudget] = useState(50);

  const radarData = {
    labels: ['Army Size', 'Naval Power', 'Air Superiority', 'Intel Network', 'Defense Infra', 'Cyber'],
    datasets: [
      {
        label: 'Valdoria (Us)',
        data: [8, 6, 7, 5, 8, 4],
        backgroundColor: 'rgba(59, 130, 246, 0.2)',
        borderColor: '#3b82f6',
        pointBackgroundColor: '#3b82f6',
        borderWidth: 2
      },
      {
        label: 'Drakmoor (AI)',
        data: [9, 8, 5, 7, 6, 8],
        backgroundColor: 'rgba(239, 68, 68, 0.2)',
        borderColor: '#ef4444',
        pointBackgroundColor: '#ef4444',
        borderWidth: 2
      }
    ]
  };

  const radarOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        grid: { color: 'rgba(255, 255, 255, 0.1)' },
        angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
        pointLabels: { color: '#94a3b8', font: { size: 11 } },
        ticks: { display: false, min: 0, max: 10 }
      }
    },
    plugins: {
      legend: { labels: { color: '#f8fafc' } }
    }
  };

  return (
    <section className="dashboard-grid">
      <div className="card col-4">
        <div className="card-header">
          <h3 className="card-title"><Target /> Threat Assessment</h3>
        </div>
        <div className="chart-container large">
          <Radar data={radarData} options={radarOptions} />
        </div>
      </div>

      <div className="card col-4">
        <div className="card-header">
          <h3 className="card-title"><UserCheck /> Intelligence Reports</h3>
        </div>
        <div className="data-list">
          <div className="data-item">
            <div className="data-item-info">
              <h4 className="text-red">Drakmoor Troop Movements</h4>
              <p>Heavy armor detected near Korvath border. Probability of invasion: High.</p>
            </div>
            <div className="data-item-value">CONFIDENTIAL</div>
          </div>
          <div className="data-item">
            <div className="data-item-info">
              <h4 className="text-blue">Solhaven Trade Leak</h4>
              <p>Intercepted corporate chatter suggests tech subsidies ending.</p>
            </div>
            <div className="data-item-value">VERIFIED</div>
          </div>
          <div className="data-item" style={{ borderLeft: '3px solid var(--accent-warning)' }}>
            <div className="data-item-info">
              <h4 className="text-yellow">Suspected Sabotage</h4>
              <p>Recent rail disruption in Northern Sector linked to foreign operatives.</p>
            </div>
            <div className="data-item-value">INVESTIGATING</div>
          </div>
        </div>
      </div>

      {/* NEW: Military Map Integration */}
      <div className="card col-4">
        <div className="card-header">
          <h3 className="card-title"><MapPin /> Deployment & Ops Map</h3>
        </div>
        <div className="map-widget" style={{ height: '350px' }}>
          <div className="map-overlay" onClick={() => window.open('/map_prototype.html', '_blank')}>
            <Expand />
            <span>Open Tactical View</span>
          </div>
          <iframe src="/map_prototype.html" className="map-iframe" scrolling="no" tabIndex="-1"></iframe>
        </div>
      </div>
      
      <div className="card col-12">
        <div className="flex-between">
          <h3 className="card-title">Military Readiness Index (DEF/ATK)</h3>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button className="btn" style={{ width: 'auto' }} onClick={onOpenProjectModal}>
              <Target size={16} /> Plan Operation
            </button>
            <button className="btn danger" style={{ width: 'auto' }}>
              <Skull size={16} /> DEFCON Settings
            </button>
          </div>
        </div>
      </div>

      <div className="card col-12">
        <div className="card-header">
          <h3 className="card-title">Military & Intel Budget Allocation (Next Round)</h3>
        </div>
        <div className="dashboard-grid" style={{ gap: '2rem' }}>
          <div className="col-6">
            <div className="input-group">
              <label>Troop Deployments ($ Millions)</label>
              <div className="range-slider-container">
                <input type="range" min="0" max="1000" value={troopBudget} onChange={(e) => setTroopBudget(Number(e.target.value))} />
                <span className="range-value">${troopBudget}M</span>
              </div>
            </div>
            <div className="input-group">
              <label>Intelligence Gathering ($ Millions)</label>
              <div className="range-slider-container">
                <input type="range" min="0" max="1000" value={intelBudget} onChange={(e) => setIntelBudget(Number(e.target.value))} />
                <span className="range-value">${intelBudget}M</span>
              </div>
            </div>
          </div>
          <div className="col-6">
            <div className="input-group">
              <label>Covert Operations ($ Millions)</label>
              <div className="range-slider-container">
                <input type="range" min="0" max="1000" value={covertBudget} onChange={(e) => setCovertBudget(Number(e.target.value))} />
                <span className="range-value">${covertBudget}M</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
