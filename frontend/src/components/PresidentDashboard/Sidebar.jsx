import React from 'react';
import { Truck, Shield, LineChart, Landmark, Globe, ArrowLeft } from 'lucide-react';
import { useGame } from '../../context/GameContext';

export default function Sidebar({ activeTab, setActiveTab }) {
  const { nation } = useGame();
  const tabs = [
    { id: 'infrastructure', label: 'Infrastructure', icon: <Truck size={20} /> },
    { id: 'intel', label: 'Intel & Military', icon: <Shield size={20} /> },
    { id: 'indexes', label: 'Indexes', icon: <LineChart size={20} /> },
    { id: 'financing', label: 'Financing', icon: <Landmark size={20} /> },
    { id: 'diplomacy', label: 'Diplomacy', icon: <Globe size={20} /> },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="nation-brand">
          <div className="flag-icon">V</div>
          <div className="nation-info">
            <h2>{nation?.name || 'Loading nation'}</h2>
            <p>{nation?.archetype || 'National government'}</p>
          </div>
        </div>
      </div>
      
      <nav className="nav-menu">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`nav-item ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.icon}
            <span style={{ marginLeft: '10px' }}>{tab.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <a href="/map_prototype.html" className="back-btn">
          <ArrowLeft size={16} /> Back to World Map
        </a>
      </div>
    </aside>
  );
}
