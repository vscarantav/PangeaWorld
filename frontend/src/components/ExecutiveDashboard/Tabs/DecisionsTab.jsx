import React, { useState } from 'react';
import NewsFeed from '../Widgets/NewsFeed';
import { useGame } from '../../../context/GameContext';

export default function DecisionsTab() {
  const { company, session, submitCompany } = useGame();
  const [price, setPrice] = useState(Number(company?.products?.Widget?.price || 299));
  const [headcount, setHeadcount] = useState(20);
  const [message, setMessage] = useState('');

  const lockDecisions = async () => {
    try {
      await submitCompany({ price, headcount });
      setMessage('Company decision saved for this round.');
    } catch (err) { setMessage(err.message); }
  };

  return (
    <div className="tab-content">
      <div className="dashboard-grid">
        <div className="card col-8">
          <div className="card-header">
            <h3 className="card-title"><i className="fa-solid fa-gavel"></i> Round {session?.current_round} Decisions</h3>
            <span style={{ fontSize: '0.8rem', background: 'rgba(59, 130, 246, 0.2)', color: 'var(--accent-primary)', padding: '0.25rem 0.75rem', borderRadius: '12px' }}>
              {session?.phase === 'company' ? 'Company phase' : `Server phase: ${session?.phase}`}
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <div className="input-group">
              <label>Product price ($)</label>
              <div className="range-slider-container">
                <span className="text-muted">$150</span>
                <input aria-label="Product price" type="range" min="150" max="600" value={price} onChange={(e) => setPrice(Number(e.target.value))} />
                <span className="range-value">${price}</span>
              </div>
            </div>
            <div className="input-group">
              <label>Hiring target</label>
              <div className="range-slider-container">
                <span className="text-muted">0</span>
                <input aria-label="Hiring target" type="range" min="0" max="100" value={headcount} onChange={(e) => setHeadcount(Number(e.target.value))} />
                <span className="range-value">{headcount} workers</span>
              </div>
            </div>
            <button className="btn" disabled={session?.phase !== 'company'} onClick={lockDecisions}>
              <i className="fa-solid fa-lock"></i> Lock In Decisions
            </button>
            {message && <p className="text-muted">{message}</p>}
          </div>
        </div>
        <div className="card col-4"><NewsFeed /></div>
      </div>
    </div>
  );
}
