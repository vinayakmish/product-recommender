/**
 * API service for communicating with the Spring Boot backend.
 */

const API_BASE = 'http://localhost:8080/api';

async function request(url, options) {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  // Products
  getProducts: () => request('/products'),
  getProductsByCategory: (category) =>
    request(`/products/category/${encodeURIComponent(category)}`),
  searchProducts: (query) =>
    request(`/products/search?query=${encodeURIComponent(query)}`),

  // Cart
  getCart: (userId) => request(`/cart/${userId}`),
  addToCart: (userId, productId, quantity = 1) =>
    request(`/cart/${userId}/add`, {
      method: 'POST',
      body: JSON.stringify({ productId, quantity }),
    }),
  removeFromCart: (userId, productId) =>
    request(`/cart/${userId}/remove/${productId}`, {
      method: 'DELETE',
    }),
  clearCart: (userId) =>
    request(`/cart/${userId}/clear`, {
      method: 'DELETE',
    }),

  // Recommendations
  trainModel: () =>
    request('/recommendations/train', { method: 'POST' }),
  getRecommendations: (userId, topN = 5) =>
    request(`/recommendations/cart/${userId}?topN=${topN}`),
  mlHealth: () => request('/recommendations/health'),
};
