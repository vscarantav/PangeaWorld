import React, { useState } from 'react';
import { Bot, X, MessageSquare, Sparkles } from 'lucide-react';

export default function AIAdvisor() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Floating Button */}
      <button 
        onClick={() => setIsOpen(true)}
        style={{
          position: 'fixed',
          bottom: '2rem',
          right: '2rem',
          background: 'var(--accent-primary)',
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
          transform: isOpen ? 'scale(0)' : 'scale(1)'
        }}
      >
        <Bot size={30} />
      </button>

      {/* Slide-out Panel */}
      <div 
        style={{
          position: 'fixed',
          top: 0,
          right: isOpen ? 0 : '-400px',
          width: '400px',
          height: '100vh',
          background: 'rgba(15, 23, 42, 0.95)',
          backdropFilter: 'var(--glass-blur)',
          borderLeft: '1px solid var(--border-light)',
          zIndex: 50,
          transition: 'right 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '-10px 0 25px rgba(0,0,0,0.5)'
        }}
      >
        <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sparkles size={20} color="var(--accent-primary)" />
            <h3 style={{ fontSize: '1.2rem' }}>Gemini Advisor</h3>
          </div>
          <button onClick={() => setIsOpen(false)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={24} />
          </button>
        </div>

        <div style={{ flex: 1, padding: '1.5rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          
          <div style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)', padding: '1rem', borderRadius: '8px', alignSelf: 'flex-start', maxWidth: '90%' }}>
            <p style={{ fontSize: '0.9rem', lineHeight: '1.5' }}>
              Greetings, Mr. President. Based on the latest Pangea Times reports, Drakmoor forces have been spotted near the Korvath border. Given our current trade dependencies with Korvath for steel, I strongly advise maintaining high readiness. 
            </p>
          </div>

          <div style={{ background: 'rgba(255, 255, 255, 0.1)', padding: '1rem', borderRadius: '8px', alignSelf: 'flex-end', maxWidth: '90%' }}>
            <p style={{ fontSize: '0.9rem' }}>What is our current FMI borrowing limit if we need to fund a rapid military expansion?</p>
          </div>

          <div style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)', padding: '1rem', borderRadius: '8px', alignSelf: 'flex-start', maxWidth: '90%' }}>
            <p style={{ fontSize: '0.9rem', lineHeight: '1.5' }}>
              Your current FMI Debt Ratio is 42%. You have room to borrow an additional <strong>$500M</strong> through an Emergency Credit line, though this will incur a 9% interest rate over the next two rounds. Alternatively, you can increase your FMI Quota now to unlock better rates next round.
            </p>
          </div>

        </div>

        <div style={{ padding: '1rem', borderTop: '1px solid var(--border-light)' }}>
          <div style={{ display: 'flex', gap: '0.5rem', background: 'rgba(0,0,0,0.3)', borderRadius: '24px', padding: '0.5rem 1rem', border: '1px solid var(--border-light)' }}>
            <input 
              type="text" 
              placeholder="Ask for strategic advice..." 
              style={{ flex: 1, background: 'transparent', border: 'none', color: 'white', outline: 'none' }}
            />
            <button style={{ background: 'none', border: 'none', color: 'var(--accent-primary)', cursor: 'pointer' }}>
              <MessageSquare size={20} />
            </button>
          </div>
        </div>

      </div>
    </>
  );
}
