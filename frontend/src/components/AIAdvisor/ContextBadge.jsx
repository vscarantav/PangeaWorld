import React from 'react';
import { useGame } from '../../context/GameContext';

export default function ContextBadge() {
  const { session } = useGame();
  
  if (!session) return null;
  
  const isEarly = session.current_round < 3;

  return (
    <div className="ai-context-badge">
      <div className="ai-context-icon">🧠</div>
      <div className="ai-context-text">
        <strong>Context: Round {session.current_round} data, your financials, and public markets.</strong>
        {isEarly && <span className="ai-context-warning"> (Early game: limited history available)</span>}
      </div>
      
      <style>{`
        .ai-context-badge {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.5rem 0.75rem;
          background: rgba(30, 41, 59, 0.5);
          border: 1px solid rgba(148, 163, 184, 0.2);
          border-radius: 0.5rem;
          font-size: 0.75rem;
          color: #94a3b8;
          margin-bottom: 1rem;
        }
        .ai-context-icon {
          font-size: 1rem;
        }
        .ai-context-warning {
          color: #fbbf24;
          font-style: italic;
        }
      `}</style>
    </div>
  );
}
