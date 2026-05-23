const API_BASE = import.meta.env.VITE_API_URL || import.meta.env.REACT_APP_API_URL || 'http://localhost:5001/api';

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `API error ${res.status}`);
  }
  return res.json();
}

export const api = {
  health: () => request('/health'),
  getProducts: () => request('/products'),
  searchProducts: (q) => request(`/products/search?q=${encodeURIComponent(q)}`),
  getProduct: (id) => request(`/products/${id}`),
  getSimilar: (id, k = 5) => request(`/similar/${id}?k=${k}`),
  getRecommendations: (userId, k = 8) => request(`/recommendations/user/${userId}?k=${k}`),
  getUsers: () => request('/users'),
  likeProduct: (userId, productId) =>
    request('/interactions', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, product_id: productId, type: 'like' }),
    }),
};
