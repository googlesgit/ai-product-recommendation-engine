import { getSessionId } from './session';

const API_BASE = import.meta.env.VITE_API_URL || import.meta.env.REACT_APP_API_URL || 'http://localhost:5001/api';

function sessionHeaders(extra = {}) {
  return {
    'Content-Type': 'application/json',
    'X-Session-Id': getSessionId(),
    ...extra,
  };
}

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: sessionHeaders(options.headers),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `API error ${res.status}`);
  }
  return res.json();
}

export const api = {
  health: () => request('/health'),
  bootstrapSession: () => request('/session', { method: 'POST' }),
  getSession: () => request('/session'),
  getProducts: () => request('/products'),
  searchProducts: (q) => request(`/products/search?q=${encodeURIComponent(q)}`),
  getSearchSuggestions: (q) =>
    request(`/products/search/suggestions?q=${encodeURIComponent(q)}`),
  getProduct: (id) => request(`/products/${id}`),
  getSimilar: (id, k = 5) => request(`/similar/${id}?k=${k}`),
  getRecommendations: (userId, k = 8) =>
    request(`/recommendations/user/${encodeURIComponent(userId)}?k=${k}`),
  getRecentViews: (userId, k = 6) =>
    request(`/interactions/recent?user_id=${encodeURIComponent(userId)}&k=${k}`),
  getDemoUsers: () => request('/users/demo'),
  recordInteraction: (userId, productId, type) =>
    request('/interactions', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, product_id: productId, type }),
    }),
  likeProduct: (userId, productId) =>
    request('/interactions', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, product_id: productId, type: 'like' }),
    }),
};
