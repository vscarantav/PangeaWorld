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
      socket.onopen = () => setConnected(true);
      socket.onmessage = (message) => {
        try {
          callbackRef.current(JSON.parse(message.data));
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
