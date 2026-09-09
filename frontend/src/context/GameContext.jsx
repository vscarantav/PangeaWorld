import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import * as api from '../api/client';
import { useSessionEvents } from '../hooks/useSessionEvents';

const GameContext = createContext(null);

export function GameProvider({ children, sessionId, membership }) {
  const [session, setSession] = useState(null);
  const [nations, setNations] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [market, setMarket] = useState(null);
  const [resourceMarket, setResourceMarket] = useState(null);
  const [news, setNews] = useState([]);
  const [selectedNationId, setSelectedNationId] = useState(null);
  const [selectedCompanyId, setSelectedCompanyId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const refresh = useCallback(async (targetSessionId) => {
    if (!targetSessionId) return;
    const [nextSession, nextNations, nextCompanies, nextMarket, nextNews] = await Promise.all([
      api.getSession(targetSessionId), api.getNations(targetSessionId), api.getCompanies(targetSessionId), api.getMarket(targetSessionId), api.getNews(targetSessionId),
    ]);
    setSession(nextSession); setNations(nextNations); setCompanies(nextCompanies); setMarket(nextMarket); setNews(nextNews.articles || []);
    setSelectedNationId((current) => current || nextNations[0]?.id || null);
    setSelectedCompanyId((current) => current || nextCompanies[0]?.id || null);
  }, []);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        if (!sessionId) return;
        const current = await api.getSession(sessionId);
        if (active) {
          await refresh(current.id);
          if (membership?.role === 'president') setSelectedNationId(membership.entity_id);
          if (membership?.role === 'executive') setSelectedCompanyId(membership.entity_id);
        }
      } catch (err) { if (active) setError(err.message); }
      finally { if (active) setLoading(false); }
    })();
    return () => { active = false; };
  }, [sessionId, membership?.role, membership?.entity_id, refresh]);

  const realtimeConnected = useSessionEvents(sessionId, () => {
    // Refresh on initial connection/reconnect too, closing the race where a
    // state change occurs while the socket is being established.
    refresh(sessionId).catch((refreshError) => setError(refreshError.message));
  });

  const advance = async () => { const result = await api.advanceRound(session.id, session.phase); await refresh(session.id); return result; };
  const saveMapSnapshot = async (snapshot) => {
    const result = await api.updateMap(session.id, snapshot);
    setSession((current) => ({ ...current, map_snapshot: result.map_snapshot }));
    return result;
  };
  const loadResourceMarket = async (resourceType, buyerNationId = null) => {
    const result = await api.getResourceMarket(session.id, resourceType, buyerNationId);
    setResourceMarket(result);
    return result;
  };
  const submitNation = (data) => api.submitNationDecision(session.id, selectedNationId, data);
  const submitCompany = (data) => api.submitCompanyDecision(session.id, selectedCompanyId, data);
  const saveCompanyDraft = (data) => api.saveCompanyDraft(session.id, selectedCompanyId, data);
  const value = useMemo(() => ({ session, nations, companies, market, resourceMarket, news,
    nation: nations.find((item) => item.id === selectedNationId) || null,
    company: companies.find((item) => item.id === selectedCompanyId) || null,
    selectedNationId, setSelectedNationId, selectedCompanyId, setSelectedCompanyId,
    membership, loading, error, realtimeConnected, refresh, advance, submitNation, submitCompany, saveCompanyDraft, saveMapSnapshot, loadResourceMarket }),
    [session, nations, companies, market, resourceMarket, news, selectedNationId, selectedCompanyId, membership, loading, error, realtimeConnected, refresh]);
  return <GameContext.Provider value={value}>{children}</GameContext.Provider>;
}

export function useGame() {
  const value = useContext(GameContext);
  if (!value) throw new Error('useGame must be used inside GameProvider');
  return value;
}
