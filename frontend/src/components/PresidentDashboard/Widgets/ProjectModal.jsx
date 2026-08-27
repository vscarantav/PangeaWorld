import React, { useState } from 'react';
import { X, Clock, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function ProjectModal({ onClose }) {
  const [timeline, setTimeline] = useState(2); // Default to standard

  const baseCost = 450;
  
  const getMultiplier = () => {
    if (timeline === 1) return 5;
    if (timeline === 2) return 2;
    return 1;
  };

  const finalCost = baseCost * getMultiplier();

  return (
    <div className="modal-overlay active">
      <div className="modal-content" style={{ maxWidth: '600px', height: 'auto', padding: '2rem' }}>
        <button className="modal-close" onClick={onClose}><X size={20} /></button>
        
        <h2 style={{ marginBottom: '1.5rem', fontSize: '1.5rem', borderBottom: '1px solid var(--border-light)', paddingBottom: '0.5rem' }}>
          Propose Project / Operation
        </h2>

        <div style={{ marginBottom: '1.5rem' }}>
          <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>
            Select the deployment timeframe. Faster deployment guarantees secrecy but costs significantly more.
          </p>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {/* 1 Round Option */}
            <div 
              onClick={() => setTimeline(1)}
              style={{ padding: '1rem', border: `1px solid ${timeline === 1 ? 'var(--accent-primary)' : 'var(--border-light)'}`, borderRadius: '8px', cursor: 'pointer', background: timeline === 1 ? 'rgba(59, 130, 246, 0.1)' : 'transparent', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
            >
              <div>
                <h4 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Clock size={16} /> 1 Round (Rush)</h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Executed immediately. Immune to foreign intel.</p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ display: 'block', fontWeight: 'bold', color: 'var(--accent-danger)' }}>5x Cost</span>
                <span style={{ fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}><ShieldCheck size={14} color="var(--accent-secondary)" /> 100% Secret</span>
              </div>
            </div>

            {/* 2 Round Option */}
            <div 
              onClick={() => setTimeline(2)}
              style={{ padding: '1rem', border: `1px solid ${timeline === 2 ? 'var(--accent-primary)' : 'var(--border-light)'}`, borderRadius: '8px', cursor: 'pointer', background: timeline === 2 ? 'rgba(59, 130, 246, 0.1)' : 'transparent', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
            >
              <div>
                <h4 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Clock size={16} /> 2 Rounds (Standard)</h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Moderate urgency. Chance of intel leak.</p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ display: 'block', fontWeight: 'bold', color: 'var(--accent-warning)' }}>2x Cost</span>
                <span style={{ fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}><AlertTriangle size={14} color="var(--accent-warning)" /> Moderate Risk</span>
              </div>
            </div>

            {/* 3 Round Option */}
            <div 
              onClick={() => setTimeline(3)}
              style={{ padding: '1rem', border: `1px solid ${timeline === 3 ? 'var(--accent-primary)' : 'var(--border-light)'}`, borderRadius: '8px', cursor: 'pointer', background: timeline === 3 ? 'rgba(59, 130, 246, 0.1)' : 'transparent', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
            >
              <div>
                <h4 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Clock size={16} /> 3 Rounds (Long-term)</h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Most cost-effective, but highly vulnerable to spying.</p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ display: 'block', fontWeight: 'bold', color: 'var(--accent-secondary)' }}>1x Cost</span>
                <span style={{ fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}><AlertTriangle size={14} color="var(--accent-danger)" /> High Risk</span>
              </div>
            </div>
          </div>
        </div>

        <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Projected Total Cost:</span>
          <span style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>${finalCost}M</span>
        </div>

        <button className="btn" onClick={onClose} style={{ width: '100%' }}>Deploy Project</button>
      </div>
    </div>
  );
}
