import React, { useState } from 'react';
import PresidentDashboard from './components/PresidentDashboard';
import ExecutiveDashboard from './components/ExecutiveDashboard';
import './index.css';

function App() {
  const [role, setRole] = useState('executive');

  return (
    <>
      <div style={{ position: 'fixed', top: '10px', left: '50%', transform: 'translateX(-50%)', zIndex: 9999, background: 'rgba(0,0,0,0.8)', padding: '5px 10px', borderRadius: '20px', border: '1px solid var(--border-light)', display: 'flex', gap: '10px' }}>
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
      </div>
      {role === 'president' ? <PresidentDashboard /> : <ExecutiveDashboard />}
    </>
  );
}

export default App;
