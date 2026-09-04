import React, { useState } from 'react';
import { Truck, Pickaxe, MapPin, Plus } from 'lucide-react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';
import GameMap from '../../GameMap';
import { useGame } from '../../../context/GameContext';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend);

export default function InfrastructureTab({ setBudget, onOpenProjectModal }) {
  const { session, saveMapSnapshot } = useGame();
  const [railBudget, setRailBudget] = useState(450);
  const [portBudget, setPortBudget] = useState(200);
  const railroadCount = session?.map_snapshot?.edges?.filter((edge) => edge.has_railroad).length || 0;
  const portCount = session?.map_snapshot?.cities?.filter((city) => city.is_port).length || 0;

  const logisticsData = {
    labels: ['Sea Freight', 'Rail', 'Air'],
    datasets: [{
      label: 'Avg Cost per Unit ($)',
      data: [2, 12, 30],
      backgroundColor: [
        'rgba(59, 130, 246, 0.8)',
        'rgba(16, 185, 129, 0.8)',
        'rgba(245, 158, 11, 0.8)'
      ],
      borderRadius: 4
    }]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      y: { grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false }, beginAtZero: true },
      x: { grid: { display: false } }
    }
  };

  const doughnutData = {
    labels: ['Railroads', 'Ports/Maritime', 'Airports'],
    datasets: [{
      data: [railBudget, portBudget, 150],
      backgroundColor: ['#3b82f6', '#10b981', '#f59e0b'],
      borderWidth: 0,
      hoverOffset: 4
    }]
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'right', labels: { color: '#f8fafc' } }
    },
    cutout: '70%'
  };

  return (
    <section className="dashboard-grid">
      
      {/* Logistics Overview */}
      <div className="card col-8">
        <div className="card-header">
          <h3 className="card-title"><Truck /> Logistics & Shipping Index</h3>
          <span className="text-muted">Avg Transit Delay: <span className="text-green">Normal</span></span>
        </div>
        <div className="chart-container">
          <Bar data={logisticsData} options={chartOptions} />
        </div>
      </div>

      {/* Current Projects */}
      <div className="card col-4">
        <div className="card-header">
          <h3 className="card-title"><Pickaxe /> Active Projects</h3>
        </div>
        <div className="data-list"><div className="data-item"><span>Railroad segments built</span><span className="data-item-value text-blue">{railroadCount}</span></div><div className="data-item"><span>Ports in map snapshot</span><span className="data-item-value text-green">{portCount}</span></div></div>
        <button className="btn" style={{ marginTop: '1.5rem' }} onClick={onOpenProjectModal}><Plus size={16} /> Propose New Project</button>
      </div>

      {/* Infrastructure Budget */}
      <div className="card col-8">
        <div className="card-header">
          <h3 className="card-title">Infrastructure Budget Allocation (Next Round)</h3>
        </div>
        <div className="dashboard-grid" style={{ gap: '2rem' }}>
          <div className="col-12">
            <div className="input-group">
              <label>Railroad Maintenance ($ Millions)</label>
              <div className="range-slider-container">
                <input type="range" min="0" max="1000" value={railBudget} onChange={(e) => setRailBudget(Number(e.target.value))} />
                <span className="range-value">${railBudget}M</span>
              </div>
            </div>
            <div className="input-group">
              <label>Port & Maritime Subsidies ($ Millions)</label>
              <div className="range-slider-container">
                <input type="range" min="0" max="1000" value={portBudget} onChange={(e) => setPortBudget(Number(e.target.value))} />
                <span className="range-value">${portBudget}M</span>
              </div>
            </div>
          </div>
          <div className="col-12">
            <div className="chart-container" style={{ height: '150px' }}>
              <Doughnut data={doughnutData} options={doughnutOptions} />
            </div>
          </div>
        </div>
      </div>

      {/* Map Connection */}
      <div className="card col-4">
        <div className="card-header">
          <h3 className="card-title"><MapPin /> Territory Map</h3>
        </div>
        <div className="map-widget">
          {session && <GameMap seed={session.seed} mapSnapshot={session.map_snapshot} onSnapshotChange={saveMapSnapshot} />}
        </div>
      </div>
    </section>
  );
}
