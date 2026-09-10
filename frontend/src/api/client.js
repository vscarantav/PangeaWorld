const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const sessionWebSocketUrl = (id) => `${API_BASE_URL.replace(/^http/, 'ws')}/api/sessions/${id}/ws`;

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
  return body;
}

export const createSession = (phaseDurationSeconds = 172800) => request('/api/sessions', {
  method: 'POST', body: JSON.stringify({ phase_duration_seconds: phaseDurationSeconds }),
});
export const getSession = (id, { includeMap = true } = {}) => request(`/api/sessions/${id}${includeMap ? '' : '?include_map=false'}`);
export const getNations = (id) => request(`/api/sessions/${id}/nations`);
export const getNation = (sessionId, nationId) => request(`/api/sessions/${sessionId}/nations/${nationId}`);
export const getCompanies = (id) => request(`/api/sessions/${id}/companies`);
export const getCompany = (sessionId, companyId) => request(`/api/sessions/${sessionId}/companies/${companyId}`);
export const getMarket = (id) => request(`/api/sessions/${id}/market`);
export const getResourceMarket = (id, resourceType, buyerNationId = null) => request(`/api/sessions/${id}/market/resources/${encodeURIComponent(resourceType)}${buyerNationId ? `?buyer_nation_id=${buyerNationId}` : ''}`);
export const getNews = (id) => request(`/api/sessions/${id}/news`);
export const getPhase3Results = (id) => request(`/api/sessions/${id}/phase3/results`);
export const updateMap = (id, mapSnapshot) => request(`/api/sessions/${id}/map`, { method: 'PUT', body: JSON.stringify({ map_snapshot: mapSnapshot }) });
export const submitNationDecision = (sessionId, nationId, decisionData) => request(`/api/sessions/${sessionId}/nations/${nationId}/decisions`, { method: 'POST', body: JSON.stringify({ decision_data: decisionData }) });
export const savePresidentialReadiness = (sessionId, nationId, decisionData) => request(`/api/sessions/${sessionId}/nations/${nationId}/readiness`, { method: 'PUT', body: JSON.stringify({ decision_data: decisionData }) });
export const submitCompanyDecision = (sessionId, companyId, decisionData) => request(`/api/sessions/${sessionId}/companies/${companyId}/decisions`, { method: 'POST', body: JSON.stringify({ decision_data: decisionData }) });
export const saveCompanyDraft = (sessionId, companyId, decisionData) => request(`/api/sessions/${sessionId}/companies/${companyId}/draft`, { method: 'PUT', body: JSON.stringify({ decision_data: decisionData }) });
export const advanceRound = (id, expected_phase) => request(`/api/sessions/${id}/advance`, { method: 'POST', body: JSON.stringify({ expected_phase }) });
export const register = (payload) => request('/api/auth/register', { method: 'POST', body: JSON.stringify(payload) });
export const login = (payload) => request('/api/auth/login', { method: 'POST', body: JSON.stringify(payload) });
export const logout = () => request('/api/auth/logout', { method: 'POST' });
export const getMe = () => request('/api/auth/me');
export const getLobby = (id) => request(`/api/sessions/${id}/lobby`);
export const joinLobby = (join_code) => request('/api/sessions/lobby/join', { method: 'POST', body: JSON.stringify({ join_code }) });
export const assignSeat = (id, payload) => request(`/api/sessions/${id}/lobby/assign`, { method: 'POST', body: JSON.stringify(payload) });
export const startLobby = (id) => request(`/api/sessions/${id}/lobby/start`, { method: 'POST' });
export const getReadiness = (id) => request(`/api/sessions/${id}/readiness`);
export const getRecoverableSessions = () => request('/api/sessions/legacy/recoverable');
export const claimLegacySession = (id) => request(`/api/sessions/${id}/claim-legacy`, { method: 'POST' });
export const renameNation = (sessionId, nationId, name) => request(`/api/sessions/${sessionId}/nations/${nationId}/name`, { method: 'PUT', body: JSON.stringify({ name }) });
export const renameCompany = (sessionId, companyId, name) => request(`/api/sessions/${sessionId}/companies/${companyId}/name`, { method: 'PUT', body: JSON.stringify({ name }) });
