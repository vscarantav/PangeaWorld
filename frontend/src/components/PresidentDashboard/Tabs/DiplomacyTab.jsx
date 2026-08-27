import React, { useState } from 'react';
import { Globe, Users, Vote, MessageSquare, Send } from 'lucide-react';

export default function DiplomacyTab() {
  const [chatMessage, setChatMessage] = useState('');
  
  const treaties = [
    { id: 1, name: "Northern Trade Pact", members: ["Valdoria", "Korvath"], type: "Trade", status: "Active" },
    { id: 2, name: "Mutual Defense Treaty", members: ["Valdoria", "Terranova"], type: "Military", status: "Active" },
    { id: 3, name: "Tech Subsidy Agreement", members: ["Valdoria", "Lunara"], type: "Economic", status: "Pending" }
  ];

  return (
    <section className="dashboard-grid">
      
      {/* Pangea Assembly (UN Forum) */}
      <div className="card col-8">
        <div className="card-header">
          <h3 className="card-title"><Globe /> Pangea Assembly</h3>
          <span className="text-muted">Global Communications Forum</span>
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', height: '400px' }}>
          <div style={{ flex: 1, background: 'rgba(0,0,0,0.2)', borderRadius: '8px', padding: '1rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1rem', border: '1px solid var(--border-light)' }}>
            
            <div style={{ alignSelf: 'flex-start', maxWidth: '80%' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Solhaven • 10:42 AM</span>
              <div style={{ background: 'rgba(255,255,255,0.1)', padding: '0.75rem', borderRadius: '8px', marginTop: '0.25rem' }}>
                We urge all nations to reconsider the proposed tariffs on financial services. Open markets benefit everyone.
              </div>
            </div>

            <div style={{ alignSelf: 'flex-start', maxWidth: '80%' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Drakmoor (AI) • 11:05 AM</span>
              <div style={{ background: 'rgba(239, 68, 68, 0.2)', border: '1px solid rgba(239, 68, 68, 0.5)', padding: '0.75rem', borderRadius: '8px', marginTop: '0.25rem' }}>
                The continued sanctions against our people are an act of economic warfare. We will not be held responsible for the consequences if these are not lifted by next quarter.
              </div>
            </div>

            <div style={{ alignSelf: 'flex-end', maxWidth: '80%' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Valdoria (You) • 11:15 AM</span>
              <div style={{ background: 'var(--accent-primary)', color: 'white', padding: '0.75rem', borderRadius: '8px', marginTop: '0.25rem' }}>
                Valdoria stands with the FMI resolution. Drakmoor must allow weapons inspectors before sanctions are lifted.
              </div>
            </div>

          </div>
          
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input 
              type="text" 
              value={chatMessage}
              onChange={(e) => setChatMessage(e.target.value)}
              placeholder="Address the assembly..." 
              style={{ flex: 1, background: 'rgba(255,255,255,0.1)', border: '1px solid var(--border-light)', color: 'white', padding: '0.75rem', borderRadius: '8px', outline: 'none' }}
            />
            <button className="btn" style={{ width: 'auto' }}><Send size={18} /></button>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }} className="col-4">
        {/* Active Treaties */}
        <div className="card">
          <div className="card-header" style={{ marginBottom: '1rem' }}>
            <h3 className="card-title"><Users /> Active Treaties</h3>
          </div>
          <div className="data-list">
            {treaties.map(t => (
              <div key={t.id} className="data-item" style={{ padding: '0.75rem' }}>
                <div className="data-item-info">
                  <h4 style={{ fontSize: '0.9rem' }}>{t.name}</h4>
                  <p style={{ fontSize: '0.75rem' }}>With: {t.members.filter(m => m !== 'Valdoria').join(', ')}</p>
                </div>
                <div className={`data-item-value ${t.status === 'Active' ? 'text-green' : 'text-yellow'}`} style={{ fontSize: '0.8rem' }}>
                  {t.status}
                </div>
              </div>
            ))}
          </div>
          <button className="btn secondary" style={{ marginTop: '1rem', padding: '0.5rem', fontSize: '0.85rem' }}>Propose Treaty</button>
        </div>

        {/* Sanctions Voting */}
        <div className="card" style={{ borderColor: 'var(--accent-warning)', background: 'rgba(245, 158, 11, 0.05)' }}>
          <div className="card-header" style={{ marginBottom: '1rem' }}>
            <h3 className="card-title"><Vote /> FMI Sanctions Vote</h3>
          </div>
          <p style={{ fontSize: '0.85rem', marginBottom: '1rem', lineHeight: '1.4' }}>
            <strong>Resolution 44-B:</strong> Impose Level 2 trade embargo on Drakmoor steel exports.
          </p>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="btn" style={{ background: 'var(--accent-secondary)' }}>Aye</button>
            <button className="btn danger">Nay</button>
            <button className="btn secondary">Abstain</button>
          </div>
        </div>
      </div>

    </section>
  );
}
