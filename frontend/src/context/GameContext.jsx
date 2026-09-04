import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import * as api from '../api/client';
import { generateMapData } from '../utils/MapGenerator';

const GameContext = createContext(null);

function serializeMapSnapshot(map, seed) {
  return {
    seed,
    triangles: map.triangles.map((triangle) => ({ id: triangle.id, terrain: triangle.terrain.name, points: triangle.points })),
    edges: map.edges.map((edge) => ({ id: edge.id, triangle_ids: edge.triangles.map((triangle) => triangle.id), has_railroad: Boolean(edge.hasRailroad), is_river: Boolean(edge.isRiver), is_impassable: Boolean(edge.isImpassable) })),
    countries: map.countries.map((country) => ({ id: country.id, name: country.name, x: country.x, y: country.y, labelX: country.labelX, labelY: country.labelY })),
  };
}

export function GameProvider({ children }) {
  const [session, setSession] = useState(null);
  const [nations, setNations] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [market, setMarket] = useState(null);
  const [news, setNews] = useState([]);
  const [selectedNationId, setSelectedNationId] = useState(null);
  const [selectedCompanyId, setSelectedCompanyId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const refresh = async (sessionId = session?.id) => {
    if (!sessionId) return;
    const [nextSession, nextNations, nextCompanies, nextMarket, nextNews] = await Promise.all([
      api.getSession(sessionId), api.getNations(sessionId), api.getCompanies(sessionId), api.getMarket(sessionId), api.getNews(sessionId),
    ]);
    setSession(nextSession); setNations(nextNations); setCompanies(nextCompanies); setMarket(nextMarket); setNews(nextNews.articles || []);
    setSelectedNationId((current) => current || nextNations[0]?.id || null);
    setSelectedCompanyId((current) => current || nextCompanies[0]?.id || null);
  };

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const seed = `local-${Date.now()}`;
        const snapshot = serializeMapSnapshot(generateMapData(seed), seed);
        const created = await api.createSession(seed, snapshot);
        if (active) await refresh(created.id);
      } catch (err) { if (active) setError(err.message); }
      finally { if (active) setLoading(false); }
    })();
    return () => { active = false; };
  }, []);

  const advance = async () => { const result = await api.advanceRound(session.id); await refresh(); return result; };
  const submitNation = (data) => api.submitNationDecision(session.id, selectedNationId, data);
  const submitCompany = (data) => api.submitCompanyDecision(session.id, selectedCompanyId, data);
  const value = useMemo(() => ({ session, nations, companies, market, news,
    nation: nations.find((item) => item.id === selectedNationId) || null,
    company: companies.find((item) => item.id === selectedCompanyId) || null,
    selectedNationId, setSelectedNationId, selectedCompanyId, setSelectedCompanyId,
    loading, error, refresh, advance, submitNation, submitCompany }),
    [session, nations, companies, market, news, selectedNationId, selectedCompanyId, loading, error]);
  return <GameContext.Provider value={value}>{children}</GameContext.Provider>;
}

export function useGame() {
  const value = useContext(GameContext);
  if (!value) throw new Error('useGame must be used inside GameProvider');
  return value;
}
