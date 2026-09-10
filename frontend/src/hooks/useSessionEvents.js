import { useEffect, useRef, useState } from 'react';
import { sessionWebSocketUrl } from '../api/client';

export function useSessionEvents(sessionId, onEvent) {
  const callbackRef = useRef(onEvent);
  const [connected, setConnected] = useState(false);
  useEffect(() => { callbackRef.current = onEvent; }, [onEvent]);

  useEffect(() => {
    if (!sessionId) return undefined;
    let active = true;
    let socket;
    let retryTimer;

    const connect = () => {
      if (!active) return;
      socket = new WebSocket(sessionWebSocketUrl(sessionId));
      // The browser-level open event can precede the server adding this socket
      // to its session broadcast set. Report Live only after the server's
      // acknowledgement, so callers cannot advance a phase into that gap.
      socket.onopen = () => setConnected(false);
      socket.onmessage = (message) => {
        try {
          const event = JSON.parse(message.data);
          if (event.type === 'connected') setConnected(true);
          callbackRef.current(event);
        } catch {
          // Ignore malformed notifications; periodic REST refresh remains active.
        }
      };
      socket.onclose = () => {
        setConnected(false);
        if (active) retryTimer = window.setTimeout(connect, 2000);
      };
    };

    connect();
    return () => {
      active = false;
      window.clearTimeout(retryTimer);
      socket?.close();
    };
  }, [sessionId]);

  return connected;
}
