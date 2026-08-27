import React from 'react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const tabs = [
    { id: 'financials', icon: 'fa-solid fa-chart-line', label: 'Financials' },
    { id: 'sourcing', icon: 'fa-solid fa-truck-fast', label: 'Sourcing' },
    { id: 'market', icon: 'fa-solid fa-store', label: 'Market' },
    { id: 'decisions', icon: 'fa-solid fa-gavel', label: 'Decisions' }
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="nation-brand">
          <div className="flag-icon" style={{ background: 'linear-gradient(135deg, #10b981, #3b82f6)' }}>
            ZI
          </div>
          <div className="nation-info">
            <h2>Zephyr Ind.</h2>
            <p>Zephyria</p>
          </div>
        </div>
      </div>
      
      <nav className="nav-menu">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`nav-item ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <i className={tab.icon}></i>
            {tab.label}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <a href="#" className="back-btn">
          <i className="fa-solid fa-arrow-right-from-bracket"></i>
          Logout
        </a>
      </div>
    </aside>
  );
}
