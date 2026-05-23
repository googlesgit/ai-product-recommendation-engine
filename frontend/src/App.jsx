import { useCallback, useEffect, useState } from 'react';
import ProductCard from './components/ProductCard';
import SearchBar from './components/SearchBar';
import { api } from './services/api';

export default function App() {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState('user_1');
  const [products, setProducts] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [similar, setSimilar] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadRecommendations = useCallback(async (userId) => {
    const data = await api.getRecommendations(userId);
    setRecommendations(data.recommendations || []);
  }, []);

  const loadSimilar = useCallback(async (productId) => {
    if (!productId) return;
    const data = await api.getSimilar(productId, 5);
    setSimilar(data.similar_products || []);
  }, []);

  useEffect(() => {
    async function init() {
      try {
        setLoading(true);
        setError(null);
        await api.health();
        const [usersRes, productsRes] = await Promise.all([
          api.getUsers(),
          api.getProducts(),
        ]);
        setUsers(usersRes.users || []);
        setProducts(productsRes.products || []);
        await loadRecommendations(selectedUser);
      } catch (e) {
        setError(e.message + ' — Is the Flask API running on port 5001?');
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  useEffect(() => {
    if (!loading && selectedUser) {
      loadRecommendations(selectedUser).catch((e) => setError(e.message));
    }
  }, [selectedUser, loading, loadRecommendations]);

  async function handleSearch(query) {
    try {
      setError(null);
      if (!query.trim()) {
        const data = await api.getProducts();
        setProducts(data.products || []);
        return;
      }
      const data = await api.searchProducts(query);
      setProducts(data.products || []);
    } catch (e) {
      setError(e.message);
    }
  }

  async function handleSelectProduct(product) {
    setSelectedProduct(product);
    try {
      await loadSimilar(product.id);
    } catch (e) {
      setError(e.message);
    }
  }

  async function handleLike(product) {
    try {
      await api.likeProduct(selectedUser, product.id);
      await loadRecommendations(selectedUser);
    } catch (e) {
      setError(e.message);
    }
  }

  if (loading) {
    return <div className="app loading">Loading recommendation engine...</div>;
  }

  return (
    <div className="app">
      <header className="header">
        <h1>AI Product Recommendation Engine</h1>
        <p>
          Personalized picks via KNN + cosine similarity · Flask API · MongoDB
        </p>
        <div className="controls">
          <label htmlFor="user-select">Demo user profile</label>
          <select
            id="user-select"
            value={selectedUser}
            onChange={(e) => setSelectedUser(e.target.value)}
          >
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name}
              </option>
            ))}
          </select>
        </div>
        <SearchBar
          value={searchQuery}
          onChange={setSearchQuery}
          onSubmit={handleSearch}
        />
      </header>

      {error && <div className="error">{error}</div>}

      <section className="section">
        <h2 className="section-title">
          For You <span className="badge">KNN + user profile</span>
        </h2>
        {recommendations.length === 0 ? (
          <p className="empty">No recommendations yet — like some products below.</p>
        ) : (
          <div className="grid">
            {recommendations.map((p) => (
              <ProductCard
                key={p.id}
                product={p}
                showScore
                onSelect={handleSelectProduct}
              />
            ))}
          </div>
        )}
      </section>

      {selectedProduct && (
        <section className="section insights-panel">
          <h2 className="section-title">
            Similarity insights <span className="badge">cosine similarity</span>
          </h2>
          <h4>Selected: {selectedProduct.name}</h4>
          <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginBottom: '0.75rem' }}>
            Products ranked by how close their feature vectors are (price, category, rating, text).
          </p>
          {similar.length === 0 ? (
            <p className="empty">No similar products found.</p>
          ) : (
            similar.map((p) => (
              <div key={p.id} className="insight-row">
                <span>{p.name}</span>
                <span className="score">
                  {(p.similarity_score * 100).toFixed(1)}% match
                </span>
              </div>
            ))
          )}
        </section>
      )}

      <section className="section">
        <h2 className="section-title">
          Browse & search <span className="badge">MongoDB + REST</span>
        </h2>
        <div className="grid">
          {products.map((p) => (
            <ProductCard
              key={p.id}
              product={p}
              selected={selectedProduct?.id === p.id}
              onSelect={handleSelectProduct}
              onLike={handleLike}
            />
          ))}
        </div>
      </section>
    </div>
  );
}
