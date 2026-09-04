import React from 'react';
import { useGame } from '../../../context/GameContext';

export default function NewsFeed() {
  const { news } = useGame();
  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="card-header"><h3 className="card-title" style={{ color: 'white' }}><i className="fa-solid fa-newspaper text-blue"></i> Pangea Times</h3></div>
      <div className="data-list" style={{ flex: 1 }}>
        {news.length === 0 && <p className="text-muted">No events reported yet. Process the first round to publish news.</p>}
        {news.map((item) => (
          <div key={item.id} className="data-item" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '0.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
              <span style={{ fontSize: '0.7rem', background: item.impact === 'High' ? 'var(--accent-danger)' : 'var(--accent-warning)', color: 'white', padding: '2px 6px', borderRadius: '4px', fontWeight: 'bold' }}>{item.impact} Impact</span>
              <span className="text-muted" style={{ fontSize: '0.75rem' }}>Round {item.round}</span>
            </div>
            <h4 style={{ fontSize: '0.9rem', lineHeight: '1.4' }}>{item.headline}</h4>
          </div>
        ))}
      </div>
    </div>
  );
}
