import React from 'react';

export default function NewsFeed() {
  const news = [
    {
      id: 1,
      headline: "Drakmoor Announces Surprise Tariffs on Tech Imports",
      impact: "High",
      impactColor: "var(--accent-danger)",
      time: "2 hours ago"
    },
    {
      id: 2,
      headline: "Valdorian Oil Output Drops Due to Storm",
      impact: "Medium",
      impactColor: "var(--accent-warning)",
      time: "5 hours ago"
    },
    {
      id: 3,
      headline: "Terranova Signs Trade Pact with Solhaven",
      impact: "Low",
      impactColor: "var(--accent-secondary)",
      time: "1 day ago"
    }
  ];

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="card-header">
        <h3 className="card-title" style={{ color: 'white' }}>
          <i className="fa-solid fa-newspaper text-blue"></i> Pangea Times
        </h3>
      </div>
      
      <div className="data-list" style={{ flex: 1 }}>
        {news.map(item => (
          <div key={item.id} className="data-item" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '0.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
              <span style={{ fontSize: '0.7rem', background: item.impactColor, color: 'white', padding: '2px 6px', borderRadius: '4px', fontWeight: 'bold' }}>
                {item.impact} Impact
              </span>
              <span className="text-muted" style={{ fontSize: '0.75rem' }}>{item.time}</span>
            </div>
            <h4 style={{ fontSize: '0.9rem', lineHeight: '1.4' }}>{item.headline}</h4>
          </div>
        ))}
      </div>
    </div>
  );
}
