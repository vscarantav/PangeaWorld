import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import * as api from '../api/client';
import { useSessionEvents } from '../hooks/useSessionEvents';

const GameContext = createContext(null);
const PHASE_ORDER = { planning: 0, presidential: 1, company: 2, processing: 3, complete: 4 };
const READINESS_ORDER = { not_started: 0, draft: 1, submitted: 2, auto_submitted: 2 };

function compareRoundPhase(left, right) {
  const roundDifference = Number(left?.round ?? left?.current_round ?? 0) - Number(right?.round ?? right?.current_round ?? 0);
  if (roundDifference) return roundDifference;
  return (PHASE_ORDER[left?.phase] ?? -1) - (PHASE_ORDER[right?.phase] ?? -1);
}

function newestSession(current, incoming) {
  if (!current) return incoming;
  return compareRoundPhase(incoming, current) >= 0 ? incoming : current;
}

function newestReadiness(current, incoming) {
  if (!current) return incoming;
  const phaseDifference = compareRoundPhase(incoming, current);
  if (phaseDifference > 0) return incoming;
  if (phaseDifference < 0) return current;
  return (READINESS_ORDER[incoming.my_status] ?? -1) >= (READINESS_ORDER[current.my_status] ?? -1)
    ? incoming
    : current;
}

export function GameProvider({ children, sessionId, membership }) {
  const [session, setSession] = useState(null);
  const [nations, setNations] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [market, setMarket] = useState(null);
  const [resourceMarket, setResourceMarket] = useState(null);
  const [news, setNews] = useState([]);
  const [phase3Results, setPhase3Results] = useState([]);
  const [readiness, setReadiness] = useState(null);
  const [selectedNationId, setSelectedNationId] = useState(null);
  const [selectedCompanyId, setSelectedCompanyId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const refresh = useCallback(async (targetSessionId) => {
    if (!targetSessionId) return;
    const [nextSession, nextNations, nextCompanies, nextMarket, nextNews, nextReadiness, nextPhase3Results] = await Promise.all([
      api.getSession(targetSessionId, { includeMap: false }), api.getNations(targetSessionId), api.getCompanies(targetSessionId), api.getMarket(targetSessionId), api.getNews(targetSessionId), api.getReadiness(targetSessionId),
      api.getPhase3Results(targetSessionId),
    ]);
    // Requests issued before a socket event can resolve afterwards. Never let
    // that older snapshot move the visible game backwards in phase or round.
    setSession((current) => newestSession(current, nextSession));
    setNations(nextNations); setCompanies(nextCompanies); setMarket(nextMarket); setNews(nextNews.articles || []);
    setReadiness((current) => newestReadiness(current, nextReadiness)); setPhase3Results(nextPhase3Results.results || []);
    setSelectedNationId((current) => current || nextNations[0]?.id || null);
    setSelectedCompanyId((current) => current || nextCompanies[0]?.id || null);
    return nextSession;
  }, []);

  const applySessionEvent = useCallback((event) => {
    if (!event?.round || !event.phase) return;
    setSession((current) => current && newestSession(current, {
      ...current, current_round: event.round, phase: event.phase,
    }));
    setReadiness((current) => current && newestReadiness(current, {
      ...current, round: event.round, phase: event.phase,
    }));
  }, []);

  const refreshLiveState = useCallback(async (targetSessionId, event) => {
    if (!targetSessionId) return;
    // Phase events are authoritative identifiers from the server. Apply them
    // immediately, then hydrate the rest of the canonical state by REST.
    applySessionEvent(event);
    const nextReadiness = await api.getReadiness(targetSessionId);
    setReadiness((current) => newestReadiness(current, nextReadiness));
    setSession((current) => current && newestSession(current, {
      ...current, current_round: nextReadiness.round, phase: nextReadiness.phase,
    }));
    return nextReadiness;
  }, [applySessionEvent]);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        if (!sessionId) return;
        // Readiness is deliberately small, unlike the session response that
        // includes the map snapshot. Render the assigned shell as soon as its
        // current phase is known, then hydrate the larger game state behind it.
        const initialReadiness = await api.getReadiness(sessionId);
        if (active) {
          setReadiness((current) => newestReadiness(current, initialReadiness));
          setSession((current) => newestSession(current, {
            id: Number(sessionId),
            current_round: initialReadiness.round,
            phase: initialReadiness.phase,
          }));
          if (membership?.role === 'president') setSelectedNationId(membership.entity_id);
          if (membership?.role === 'executive') setSelectedCompanyId(membership.entity_id);
          setLoading(false);
        }
        await refresh(sessionId);
      } catch (err) { if (active) setError(err.message); }
      finally { if (active) setLoading(false); }
    })();
    return () => { active = false; };
  }, [sessionId, membership?.role, membership?.entity_id, refresh]);

  const realtimeConnected = useSessionEvents(sessionId, (event) => {
    // A lightweight authoritative phase/readiness fetch updates controls
    // immediately. Only events that change shared game data need the larger
    // map/dashboard refresh.
    refreshLiveState(sessionId, event)
      .then(() => {
        if (["phase_changed", "results_published", "map_changed"].includes(event?.type)) {
          return refresh(sessionId);
        }
        return undefined;
      })
      .catch((refreshError) => setError(refreshError.message));
  });

  useEffect(() => {
    if (!sessionId) return undefined;
    // WebSocket delivery is the fast path, while REST is authoritative. A
    // lightweight readiness check closes short reconnect windows without
    // repeatedly downloading the multi-megabyte map snapshot.
    const pollReadiness = () => {
      const before = { round: session?.current_round, phase: session?.phase };
      refreshLiveState(sessionId)
        .then((nextReadiness) => {
          if (compareRoundPhase(nextReadiness, before) > 0) return refresh(sessionId);
          return undefined;
        })
        .catch((refreshError) => setError(refreshError.message));
    };
    const timer = window.setInterval(pollReadiness, 2000);
    return () => window.clearInterval(timer);
  }, [sessionId, session?.current_round, session?.phase, refreshLiveState, refresh]);

  const advance = useCallback(async () => { const result = await api.advanceRound(session.id, session.phase); await refresh(session.id); return result; }, [refresh, session]);
  const saveMapSnapshot = useCallback(async (snapshot) => {
    const result = await api.updateMap(session.id, snapshot);
    setSession((current) => ({ ...current, map_snapshot: result.map_snapshot }));
    return result;
  }, [session]);
  const loadMapSnapshot = useCallback(async () => {
    const nextSession = await api.getSession(session.id);
    setSession((current) => newestSession(current, nextSession));
    return nextSession.map_snapshot;
  }, [session]);
  const loadResourceMarket = useCallback(async (resourceType, buyerNationId = null) => {
    const result = await api.getResourceMarket(session.id, resourceType, buyerNationId);
    setResourceMarket(result);
    return result;
  }, [session]);
  const submitNation = useCallback(async (data) => { const result = await api.submitNationDecision(session.id, selectedNationId, data); await refresh(session.id); return result; }, [refresh, selectedNationId, session]);
  const savePresidentialReadiness = useCallback(async (data) => { const result = await api.savePresidentialReadiness(session.id, selectedNationId, data); await refresh(session.id); return result; }, [refresh, selectedNationId, session]);
  const submitCompany = useCallback(async (data) => { const result = await api.submitCompanyDecision(session.id, selectedCompanyId, data); await refresh(session.id); return result; }, [refresh, selectedCompanyId, session]);
  const saveCompanyDraft = useCallback(async (data) => { const result = await api.saveCompanyDraft(session.id, selectedCompanyId, data); await refresh(session.id); return result; }, [refresh, selectedCompanyId, session]);
  const value = useMemo(() => ({ session, nations, companies, market, resourceMarket, news, phase3Results, readiness,
    nation: nations.find((item) => item.id === selectedNationId) || null,
    company: companies.find((item) => item.id === selectedCompanyId) || null,
    selectedNationId, setSelectedNationId, selectedCompanyId, setSelectedCompanyId,
    membership, loading, error, realtimeConnected, refresh, advance, submitNation, savePresidentialReadiness, submitCompany, saveCompanyDraft, saveMapSnapshot, loadMapSnapshot, loadResourceMarket }),
    [session, nations, companies, market, resourceMarket, news, phase3Results, readiness, selectedNationId, selectedCompanyId, membership, loading, error, realtimeConnected, refresh, advance, loadMapSnapshot, loadResourceMarket, saveCompanyDraft, saveMapSnapshot, savePresidentialReadiness, submitCompany, submitNation]);
  return <GameContext.Provider value={value}>{children}</GameContext.Provider>;
}

// This module deliberately exports both the provider component and its hook.
// oxlint-disable-next-line react/only-export-components
export function useGame() {
  const value = useContext(GameContext);
  if (!value) throw new Error('useGame must be used inside GameProvider');
  return value;
}
