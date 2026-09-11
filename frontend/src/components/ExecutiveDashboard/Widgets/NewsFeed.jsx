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
            <small className="text-muted">{item.category}{item.generation === "gemini" ? " · AI-written; verify against sources" : ""}</small>
            {item.summary && <p className="text-muted" style={{ fontSize: '0.78rem' }}>{item.summary}</p>}
            {item.sources && <><svg viewBox="0 0 320 150" role="img" aria-label="Consumer price index by nation" style={{ width: '100%', maxWidth: 400 }}>
              {item.sources.filter((source) => source.cpi != null).map((source, index) => <g key={source.id}><title>Nation {source.nation_id}: CPI {source.cpi.toFixed(2)}</title><rect x={index * 38 + 5} y={130 - Math.min(120, source.cpi * 0.7)} width="25" height={Math.min(120, source.cpi * 0.7)} fill="#60a5fa" /><text x={index * 38 + 6} y="145" fill="white" fontSize="9">{source.nation_id}</text></g>)}
              </svg><details><summary>Published source data</summary><table><thead><tr><th>Nation</th><th>GDP</th><th>CPI</th><th>Trade balance</th></tr></thead><tbody>{item.sources.filter((source) => source.gdp != null).map((source) => <tr key={source.id}><td>{source.nation_id}</td><td>{source.gdp.toFixed(2)}</td><td>{source.cpi.toFixed(2)}</td><td>{source.trade_balance.toFixed(2)}</td></tr>)}</tbody></table><p>Compare the article's claims with these recorded outcomes. Bars show CPI from zero, capped at 171; use the table for exact values.</p></details></>}
          </div>
        ))}
      </div>
    </div>
  );
}
