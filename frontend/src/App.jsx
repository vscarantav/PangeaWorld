import React, { useState } from 'react';
import PresidentDashboard from './components/PresidentDashboard';
import ExecutiveDashboard from './components/ExecutiveDashboard';
import GameMap from './components/GameMap';
import './index.css';
import { GameProvider, useGame } from './context/GameContext';

function GameShell() {
  const { loading, error, session, nation, company, advance } = useGame();

  const [role, setRole] = useState('executive');
  const [isPlanningMode, setIsPlanningMode] = useState(false);

  if (loading) return <div style={{ padding: '3rem', color: 'white' }}>Connecting to PangeaWorld server…</div>;
  if (error) return <div style={{ padding: '3rem', color: '#f87171' }}>Unable to connect to the game server: {error}</div>;
  return (
    <>
      <div style={{ position: 'fixed', top: '10px', left: '50%', transform: 'translateX(-50%)', zIndex: 9999, background: 'rgba(0,0,0,0.8)', padding: '5px 10px', borderRadius: '20px', border: '1px solid var(--border-light)', display: 'flex', gap: '10px', alignItems: 'center' }}>
        <button 
          onClick={() => setRole('president')} 
          style={{ background: role === 'president' ? 'var(--accent-primary)' : 'transparent', color: 'white', border: 'none', padding: '5px 15px', borderRadius: '15px', cursor: 'pointer', fontWeight: 'bold' }}
        >
          President
        </button>
        <button 
          onClick={() => setRole('executive')} 
          style={{ background: role === 'executive' ? 'var(--accent-primary)' : 'transparent', color: 'white', border: 'none', padding: '5px 15px', borderRadius: '15px', cursor: 'pointer', fontWeight: 'bold' }}
        >
          Executive
        </button>
        <button 
          onClick={() => setRole('map')} 
          style={{ background: role === 'map' ? 'var(--accent-primary)' : 'transparent', color: 'white', border: 'none', padding: '5px 15px', borderRadius: '15px', cursor: 'pointer', fontWeight: 'bold' }}
        >
          Map View
        </button>
        
        {role === 'map' && (
            <>
                <div style={{ width: '1px', height: '20px', background: 'var(--border-light)', margin: '0 5px' }}></div>
                <button 
                onClick={() => setIsPlanningMode(!isPlanningMode)} 
                style={{ background: isPlanningMode ? '#e67e22' : 'transparent', color: 'white', border: '1px solid #e67e22', padding: '5px 15px', borderRadius: '15px', cursor: 'pointer', fontWeight: 'bold' }}
                >
                {isPlanningMode ? 'Exit Planning Mode' : 'Plan Roads'}
                </button>
            </>
        )}
      </div>
      
        <div style={{ position: 'fixed', bottom: 16, left: 16, zIndex: 9999, background: 'rgba(15,23,42,.95)', padding: '10px 14px', borderRadius: 8, color: 'white', border: '1px solid var(--border-light)' }}>
          Round {session.current_round} · {session.phase} · {nation?.name || 'No nation'} · {company?.name || 'No company'}
          {session.phase !== 'complete' && <button className="btn" style={{ marginLeft: 12, padding: '5px 10px' }} onClick={advance}>Advance phase</button>}
        </div>
      {role === 'president' && <PresidentDashboard />}
      {role === 'executive' && <ExecutiveDashboard />}
      {role === 'map' && (
          <div style={{ width: '100vw', height: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center', backgroundColor: '#1e1e1e' }}>
              <GameMap seed={session.seed} isPlanningMode={isPlanningMode} />
          </div>
      )}
    </>
  );
}

function App() {
  return <GameProvider><GameShell /></GameProvider>;
}

export default App;
