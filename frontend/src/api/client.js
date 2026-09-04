const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
  return body;
}

export const createSession = (seed = null, mapSnapshot = null) => request('/api/sessions', { method: 'POST', body: JSON.stringify({ ...(seed ? { seed } : {}), ...(mapSnapshot ? { map_snapshot: mapSnapshot } : {}) }) });
export const getSession = (id) => request(`/api/sessions/${id}`);
export const getNations = (id) => request(`/api/sessions/${id}/nations`);
export const getNation = (sessionId, nationId) => request(`/api/sessions/${sessionId}/nations/${nationId}`);
export const getCompanies = (id) => request(`/api/sessions/${id}/companies`);
export const getCompany = (sessionId, companyId) => request(`/api/sessions/${sessionId}/companies/${companyId}`);
export const getMarket = (id) => request(`/api/sessions/${id}/market`);
export const getResourceMarket = (id, resourceType) => request(`/api/sessions/${id}/market/resources/${encodeURIComponent(resourceType)}`);
export const getNews = (id) => request(`/api/sessions/${id}/news`);
export const updateMap = (id, mapSnapshot) => request(`/api/sessions/${id}/map`, { method: 'PUT', body: JSON.stringify({ map_snapshot: mapSnapshot }) });
export const submitNationDecision = (sessionId, nationId, decisionData) => request(`/api/sessions/${sessionId}/nations/${nationId}/decisions`, { method: 'POST', body: JSON.stringify({ decision_data: decisionData }) });
export const submitCompanyDecision = (sessionId, companyId, decisionData) => request(`/api/sessions/${sessionId}/companies/${companyId}/decisions`, { method: 'POST', body: JSON.stringify({ decision_data: decisionData }) });
export const advanceRound = (id) => request(`/api/sessions/${id}/advance`, { method: 'POST' });
