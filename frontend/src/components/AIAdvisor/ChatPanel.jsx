import React, { useState, useEffect, useRef } from 'react';
import { useGame } from '../../context/GameContext';
import { getChatHistory, clearChatHistory, getRateLimit, API_BASE_URL } from '../../api/client';
import ContextBadge from './ContextBadge';

const STARTER_PROMPTS_PRESIDENT = [
  "What are the trade-offs of raising tariffs this round?",
  "How will my military spending affect the approval rating long-term?",
  "What should I consider before taking on more FMI debt?",
  "What is the opportunity cost of prioritizing infrastructure over defense?",
];

const STARTER_PROMPTS_EXECUTIVE = [
  "Should I prioritize R&D or marketing this round?",
  "How does my current supplier choice affect supply chain risk?",
  "What are the trade-offs of lowering my price to gain market share?",
  "What happens to my cash flow if I increase production by 20%?",
];

function formatTime(isoString) {
  if (!isoString) return '';
  const d = new Date(isoString);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function ChatPanel({ isOpen, onClose }) {
  const { session, membership } = useGame();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [providerDown, setProviderDown] = useState(false);
  const [rateLimitInfo, setRateLimitInfo] = useState({ remaining: 20, limit: 20 });
  const messagesEndRef = useRef(null);

  // Infer role from session membership
  const role = membership?.role || 'president';
  const starterPrompts = role === 'executive' ? STARTER_PROMPTS_EXECUTIVE : STARTER_PROMPTS_PRESIDENT;

  useEffect(() => {
    if (isOpen && session?.id) {
      loadHistory();
      loadRateLimit();
    }
  }, [isOpen, session?.id]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadHistory = async () => {
    try {
      const history = await getChatHistory(session.id);
      setMessages(history);
      setError(null);
    } catch (err) {
      setError('Could not load history. The server may be unavailable.');
    }
  };

  const loadRateLimit = async () => {
    try {
      const data = await getRateLimit(session.id);
      setRateLimitInfo(data);
    } catch (_) {
      // Non-fatal
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleClear = async () => {
    if (!confirm('Are you sure you want to clear your chat history? This cannot be undone.')) return;
    try {
      await clearChatHistory(session.id);
      setMessages([]);
      await loadRateLimit();
    } catch (err) {
      setError('Failed to clear history. Please try again.');
    }
  };

  const sendMessage = async (promptText) => {
    if (!promptText.trim() || isLoading) return;
    setError(null);
    setProviderDown(false);
    setInput('');

    const userMsg = { role: 'user', content: promptText, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    const assistantPlaceholder = { role: 'assistant', content: '', timestamp: new Date().toISOString(), streaming: true };
    setMessages(prev => [...prev, assistantPlaceholder]);

    try {
      const response = await fetch(`${API_BASE_URL}/api/sessions/${session.id}/advisor/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ prompt: promptText })
      });

      if (!response.ok) {
        if (response.status === 503) {
          setProviderDown(true);
          setMessages(prev => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              content: 'The AI advisor is temporarily unavailable. Please try again in a moment.',
              streaming: false,
              isError: true
            };
            return updated;
          });
          return;
        }
        throw new Error(`Server error: ${response.status}`);
      }

      // Read remaining prompts from response header
      const remainingHeader = response.headers.get('X-Prompts-Remaining');
      if (remainingHeader !== null) {
        setRateLimitInfo(prev => ({ ...prev, remaining: parseInt(remainingHeader, 10) }));
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let accumulated = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        accumulated += decoder.decode(value, { stream: true });
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = { ...updated[updated.length - 1], content: accumulated };
          return updated;
        });
      }

      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = { ...updated[updated.length - 1], streaming: false };
        return updated;
      });

    } catch (err) {
      console.error('Streaming failed:', err);
      if (err.message?.includes('Failed to fetch')) {
        setProviderDown(true);
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            content: 'The AI advisor is currently unreachable. Check your connection and try again.',
            streaming: false,
            isError: true
          };
          return updated;
        });
      } else {
        setError('Something went wrong. Please try again.');
        setMessages(prev => prev.slice(0, -1)); // remove placeholder
      }
    } finally {
      setIsLoading(false);
      loadRateLimit();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleStarterClick = (prompt) => {
    sendMessage(prompt);
  };

  const ratePct = rateLimitInfo.limit > 0 ? (rateLimitInfo.remaining / rateLimitInfo.limit) * 100 : 100;
  const rateLimitColor = ratePct > 50 ? '#22c55e' : ratePct > 20 ? '#f59e0b' : '#ef4444';

  if (!isOpen) return null;

  return (
    <div className="chat-panel-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="chat-panel">
        {/* Header */}
        <div className="chat-header">
          <div className="chat-title">
            <span className="ai-icon">✨</span>
            <span>Gemini Advisor</span>
          </div>
          <div className="chat-header-right">
            {/* Rate limit indicator */}
            <div className="rate-limit-pill" title={`${rateLimitInfo.remaining} of ${rateLimitInfo.limit} prompts remaining this phase`}>
              <div className="rate-limit-bar" style={{ width: `${ratePct}%`, background: rateLimitColor }} />
              <span className="rate-limit-text">{rateLimitInfo.remaining}/{rateLimitInfo.limit}</span>
            </div>
            <button className="icon-btn" onClick={handleClear} title="Clear history">🗑️</button>
            <button className="icon-btn" onClick={onClose} title="Close">✕</button>
          </div>
        </div>

        {/* Error banner */}
        {(error || providerDown) && (
          <div className="error-banner">
            <span>⚠️</span>
            <span>{providerDown ? '🔌 AI Advisor temporarily unavailable' : error}</span>
            <button onClick={() => { setError(null); setProviderDown(false); }}>✕</button>
          </div>
        )}

        {/* Content */}
        <div className="chat-content">
          <ContextBadge />

          <div className="message-list">
            {messages.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">👋</div>
                <h3>How can I help you lead?</h3>
                <p>Ask me about strategy, trade-offs, or your current situation.</p>
                <div className="starter-prompts">
                  {starterPrompts.map((p, i) => (
                    <button key={i} className="starter-btn" onClick={() => handleStarterClick(p)} disabled={isLoading}>
                      {p}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div key={idx} className={`message ${msg.role}${msg.isError ? ' error' : ''}`}>
                  <div className="message-avatar">
                    {msg.role === 'user' ? '👤' : '✨'}
                  </div>
                  <div className="message-body">
                    <div className="message-bubble">
                      {msg.content}
                      {msg.streaming && <span className="typing-cursor" />}
                    </div>
                    <div className="message-meta">
                      {msg.round && <span className="round-badge">Round {msg.round}</span>}
                      {msg.timestamp && <span className="message-time">{formatTime(msg.timestamp)}</span>}
                    </div>
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input */}
        <form className="chat-input-area" onSubmit={handleSubmit}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={rateLimitInfo.remaining === 0 ? 'Prompt limit reached for this phase' : 'Ask about strategy, trade-offs, or market conditions...'}
            disabled={isLoading || rateLimitInfo.remaining === 0}
            autoComplete="off"
          />
          <button type="submit" disabled={!input.trim() || isLoading || rateLimitInfo.remaining === 0} className="send-btn">
            {isLoading ? <span className="spinner" /> : '↑'}
          </button>
        </form>
      </div>

      <style>{`
        .chat-panel-overlay {
          position: fixed;
          inset: 0;
          background: rgba(15, 23, 42, 0.5);
          z-index: 1000;
          display: flex;
          justify-content: flex-end;
          backdrop-filter: blur(4px);
        }

        .chat-panel {
          width: 420px;
          max-width: 100vw;
          height: 100%;
          background: #0f172a;
          border-left: 1px solid rgba(148, 163, 184, 0.2);
          display: flex;
          flex-direction: column;
          box-shadow: -4px 0 32px rgba(0,0,0,0.6);
          animation: slideIn 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }

        @keyframes slideIn {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }

        .chat-header {
          padding: 0.875rem 1.25rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 1px solid rgba(148, 163, 184, 0.1);
          background: rgba(30, 41, 59, 0.9);
          gap: 0.75rem;
          flex-shrink: 0;
        }

        .chat-title {
          font-weight: 600;
          color: #f8fafc;
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 1rem;
        }

        .chat-header-right {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          flex-shrink: 0;
        }

        .rate-limit-pill {
          position: relative;
          height: 1.5rem;
          min-width: 5rem;
          background: rgba(0,0,0,0.3);
          border-radius: 1rem;
          border: 1px solid rgba(148, 163, 184, 0.2);
          overflow: hidden;
          cursor: default;
        }

        .rate-limit-bar {
          position: absolute;
          top: 0; left: 0; bottom: 0;
          border-radius: 1rem;
          transition: width 0.4s ease, background 0.4s ease;
          opacity: 0.35;
        }

        .rate-limit-text {
          position: relative;
          z-index: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100%;
          font-size: 0.7rem;
          font-weight: 600;
          color: #e2e8f0;
          padding: 0 0.5rem;
        }

        .icon-btn {
          background: transparent;
          border: none;
          color: #94a3b8;
          cursor: pointer;
          padding: 0.35rem;
          border-radius: 0.25rem;
          font-size: 0.9rem;
          line-height: 1;
          transition: color 0.15s, background 0.15s;
        }

        .icon-btn:hover {
          background: rgba(148, 163, 184, 0.1);
          color: #f8fafc;
        }

        .error-banner {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.625rem 1rem;
          background: rgba(239, 68, 68, 0.15);
          border-bottom: 1px solid rgba(239, 68, 68, 0.3);
          font-size: 0.8rem;
          color: #fca5a5;
          flex-shrink: 0;
        }

        .error-banner button {
          margin-left: auto;
          background: none;
          border: none;
          color: #fca5a5;
          cursor: pointer;
          font-size: 0.85rem;
        }

        .chat-content {
          flex: 1;
          overflow-y: auto;
          padding: 1.25rem;
          display: flex;
          flex-direction: column;
          scroll-behavior: smooth;
        }

        .message-list {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .empty-state {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
          color: #94a3b8;
          gap: 0.5rem;
        }

        .empty-icon { font-size: 2.5rem; margin-bottom: 0.5rem; }
        .empty-state h3 { color: #e2e8f0; font-size: 1.1rem; margin: 0; }
        .empty-state p { font-size: 0.875rem; margin: 0 0 1rem; }

        .starter-prompts {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
          width: 100%;
          max-width: 340px;
        }

        .starter-btn {
          background: rgba(30, 41, 59, 0.7);
          border: 1px solid rgba(148, 163, 184, 0.2);
          border-radius: 0.75rem;
          padding: 0.6rem 0.875rem;
          color: #cbd5e1;
          font-size: 0.825rem;
          text-align: left;
          cursor: pointer;
          transition: background 0.15s, border-color 0.15s, color 0.15s;
          line-height: 1.4;
        }

        .starter-btn:hover:not(:disabled) {
          background: rgba(139, 92, 246, 0.15);
          border-color: rgba(139, 92, 246, 0.5);
          color: #e2e8f0;
        }

        .starter-btn:disabled { opacity: 0.4; cursor: not-allowed; }

        .message {
          display: flex;
          gap: 0.625rem;
          max-width: 92%;
        }

        .message.user {
          align-self: flex-end;
          flex-direction: row-reverse;
        }

        .message-avatar {
          width: 1.875rem;
          height: 1.875rem;
          border-radius: 50%;
          background: rgba(30, 41, 59, 0.9);
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          font-size: 0.9rem;
        }

        .message.assistant .message-avatar {
          background: linear-gradient(135deg, #8b5cf6, #ec4899);
        }

        .message-body {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }

        .message.user .message-body {
          align-items: flex-end;
        }

        .message-bubble {
          background: rgba(30, 41, 59, 0.7);
          padding: 0.625rem 0.875rem;
          border-radius: 1rem;
          color: #f1f5f9;
          font-size: 0.9rem;
          line-height: 1.55;
          white-space: pre-wrap;
          border: 1px solid rgba(148, 163, 184, 0.1);
          word-break: break-word;
          position: relative;
        }

        .message.user .message-bubble {
          background: #3b82f6;
          border-color: transparent;
        }

        .message.error .message-bubble {
          background: rgba(239, 68, 68, 0.12);
          border-color: rgba(239, 68, 68, 0.3);
          color: #fca5a5;
        }

        .typing-cursor {
          display: inline-block;
          width: 2px;
          height: 1em;
          background: #94a3b8;
          margin-left: 2px;
          vertical-align: text-bottom;
          animation: blink 0.8s step-end infinite;
        }

        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }

        .message-meta {
          display: flex;
          align-items: center;
          gap: 0.375rem;
          padding: 0 0.25rem;
        }

        .round-badge {
          background: rgba(139, 92, 246, 0.2);
          border: 1px solid rgba(139, 92, 246, 0.35);
          border-radius: 0.375rem;
          padding: 0.05rem 0.375rem;
          font-size: 0.65rem;
          color: #c4b5fd;
          font-weight: 600;
          letter-spacing: 0.01em;
        }

        .message-time {
          font-size: 0.65rem;
          color: #64748b;
        }

        .chat-input-area {
          padding: 0.875rem 1rem;
          border-top: 1px solid rgba(148, 163, 184, 0.1);
          background: rgba(15, 23, 42, 0.95);
          display: flex;
          gap: 0.625rem;
          align-items: center;
          flex-shrink: 0;
        }

        .chat-input-area input {
          flex: 1;
          background: rgba(30, 41, 59, 0.8);
          border: 1px solid rgba(148, 163, 184, 0.25);
          border-radius: 1.5rem;
          padding: 0.625rem 1.125rem;
          color: #f8fafc;
          font-size: 0.9rem;
          outline: none;
          transition: border-color 0.2s;
          min-width: 0;
        }

        .chat-input-area input:focus {
          border-color: #8b5cf6;
        }

        .chat-input-area input:disabled {
          opacity: 0.5;
        }

        .chat-input-area input::placeholder {
          color: #475569;
        }

        .send-btn {
          width: 2.5rem;
          height: 2.5rem;
          flex-shrink: 0;
          border-radius: 50%;
          background: linear-gradient(135deg, #8b5cf6, #ec4899);
          border: none;
          color: white;
          font-size: 1.1rem;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: transform 0.15s, opacity 0.15s;
        }

        .send-btn:hover:not(:disabled) { transform: scale(1.07); }
        .send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

        .spinner {
          width: 1rem;
          height: 1rem;
          border: 2px solid rgba(255,255,255,0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: spin 0.6s linear infinite;
          display: block;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        @media (max-width: 480px) {
          .chat-panel { width: 100vw; border-left: none; }
          .rate-limit-pill { min-width: 3.5rem; }
        }
      `}</style>
    </div>
  );
}
