import React, { useState } from 'react';
import ChatPanel from './ChatPanel';

export default function AIAdvisor() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button 
        onClick={() => setIsOpen(true)}
        style={{
          position: 'fixed',
          bottom: '2rem',
          right: '2rem',
          background: 'var(--accent-primary, #3b82f6)',
          color: 'white',
          border: 'none',
          borderRadius: '50%',
          width: '60px',
          height: '60px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          boxShadow: '0 4px 15px rgba(59, 130, 246, 0.5)',
          zIndex: 40,
          transition: 'transform 0.2s',
          transform: isOpen ? 'scale(0)' : 'scale(1)',
          fontSize: '1.5rem'
        }}
        title="Open AI Advisor"
      >
        ✨
      </button>

      <ChatPanel isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </>
  );
}
