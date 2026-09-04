import React, { useState } from 'react';
import { Mail } from 'lucide-react';
import { useGame } from '../../context/GameContext';

export default function Topbar({ budget }) {
  const { nation, session } = useGame();
  const [showInbox, setShowInbox] = useState(false);

  const requests = [];
  const availableBudget = Number(nation?.treasury ?? budget ?? 0);

  return (
    <header className="topbar">
      <div className="topbar-title">
        <h1>Presidential Terminal <span style={{ color: 'var(--text-muted)', fontSize: '1rem', fontWeight: 'normal', marginLeft: '10px' }}>Round {session?.current_round}</span></h1>
      </div>
      <div className="kpi-container">
        
        {/* Inbox Dropdown */}
        <div style={{ position: 'relative', marginRight: '1rem' }}>
          <button 
            style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer', position: 'relative' }}
            onClick={() => setShowInbox(!showInbox)}
          >
            <Mail size={24} />
            <span style={{ position: 'absolute', top: -5, right: -5, background: 'var(--accent-danger)', borderRadius: '50%', width: 18, height: 18, fontSize: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {requests.length}
            </span>
          </button>
          
          {showInbox && (
            <div style={{ position: 'absolute', top: '100%', right: 0, width: '350px', background: 'var(--bg-panel)', border: '1px solid var(--border-light)', borderRadius: '8px', padding: '1rem', marginTop: '1rem', zIndex: 50, backdropFilter: 'var(--glass-blur)' }}>
              <h3 style={{ marginBottom: '1rem', fontSize: '1rem', borderBottom: '1px solid var(--border-light)', paddingBottom: '0.5rem' }}>Lobbying Requests</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {requests.length === 0 && <p className="text-muted">No lobbying requests recorded for this session.</p>}
                {requests.map(req => (
                  <div key={req.id} style={{ background: 'rgba(0,0,0,0.3)', padding: '0.75rem', borderRadius: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                      {req.type === 'urgent' ? <AlertCircle size={16} color="var(--accent-danger)" /> : <Briefcase size={16} color="var(--accent-primary)" />}
                      <span style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>{req.company}</span>
                    </div>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{req.request}</p>
                    <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
                      <button className="btn" style={{ padding: '0.4rem', fontSize: '0.8rem' }}>Acknowledge</button>
                      <button className="btn secondary" style={{ padding: '0.4rem', fontSize: '0.8rem' }}>Dismiss</button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="kpi">
          <span className="kpi-label">Available Budget</span>
          <span className={`kpi-value ${budget >= 0 ? 'text-green' : 'text-red'}`}>
            ${availableBudget.toLocaleString()}M
          </span>
        </div>
        <div className="kpi">
          <span className="kpi-label">Trade Balance</span>
          <span className="kpi-value text-green">${Number(nation?.trade_balance || 0).toLocaleString()}M</span>
        </div>
        <div className="kpi">
          <span className="kpi-label">National GDP</span>
          <span className="kpi-value text-green">${Number(nation?.gdp || 0).toLocaleString()}M</span>
        </div>
        <div className="kpi">
          <span className="kpi-label">Approval Rating</span>
          <span className="kpi-value">Not tracked</span>
        </div>
        <div className="kpi">
          <span className="kpi-label">FMI Debt Ratio</span>
          <span className="kpi-value text-yellow">Not tracked</span>
        </div>
      </div>
    </header>
  );
}
