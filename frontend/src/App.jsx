import { useCallback, useEffect, useState } from 'react';
import ProductCard from './components/ProductCard';
import SearchBar from './components/SearchBar';
import Toast from './components/Toast';
import { useDebouncedValue } from './hooks/useDebouncedValue';
import { api } from './services/api';

const POPULAR_SEARCHES = ['headphones', 'microwave', 'yoga', 'books', 'electronics', 'skincare'];

export default function App() {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState('user_1');
  const [catalog, setCatalog] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [activeSearch, setActiveSearch] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [similar, setSimilar] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState('');
  const [stats, setStats] = useState(null);

  const debouncedQuery = useDebouncedValue(searchQuery, 450);
  const searchMode = activeSearch.trim().length > 0;

  const loadRecommendations = useCallback(async (userId) => {
    const data = await api.getRecommendations(userId);
    setRecommendations(data.recommendations || []);
  }, []);

  const loadSimilar = useCallback(async (productId) => {
    if (!productId) return;
    const data = await api.getSimilar(productId, 5);
    setSimilar(data.similar_products || []);
  }, []);

  const runSearch = useCallback(async (query) => {
    const q = query.trim();
    setActiveSearch(q);
    if (!q) {
      setSearchResults([]);
      setSearching(false);
      return;
    }
    try {
      setSearching(true);
      setError(null);
      const data = await api.searchProducts(q);
      setSearchResults(data.products || []);
    } catch (e) {
      setError(e.message);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  }, []);

  const clearSearch = useCallback(() => {
    setSearchQuery('');
    setActiveSearch('');
    setSearchResults([]);
    setSuggestions([]);
  }, []);

  useEffect(() => {
    async function init() {
      try {
        setLoading(true);
        setError(null);
        const health = await api.health();
        setStats(health);
        const [usersRes, productsRes] = await Promise.all([
          api.getUsers(),
          api.getProducts(),
        ]);
        setUsers(usersRes.users || []);
        setCatalog(productsRes.products || []);
        await loadRecommendations(selectedUser);
      } catch (e) {
        setError(e.message + ' — Is the Flask API running on port 5001?');
      } finally {
        setLoading(false);
      }
    }
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mount only
  }, []);

  useEffect(() => {
    if (!loading && selectedUser) {
      loadRecommendations(selectedUser).catch((e) => setError(e.message));
    }
  }, [selectedUser, loading, loadRecommendations]);

  useEffect(() => {
    if (loading) return;
    runSearch(debouncedQuery);
  }, [debouncedQuery, loading, runSearch]);

  useEffect(() => {
    const q = searchQuery.trim();
    if (!q || q.length < 2) {
      setSuggestions([]);
      return;
    }
    let cancelled = false;
    api
      .getSearchSuggestions(q)
      .then((data) => {
        if (!cancelled) setSuggestions(data.suggestions || []);
      })
      .catch(() => {
        if (!cancelled) setSuggestions([]);
      });
    return () => {
      cancelled = true;
    };
  }, [searchQuery]);

  useEffect(() => {
    if (!toast) return;
    const id = setTimeout(() => setToast(''), 3200);
    return () => clearTimeout(id);
  }, [toast]);

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
      setToast(`Liked “${product.name}” — refreshing your recommendations`);
    } catch (e) {
      setError(e.message);
    }
  }

  function handlePickSuggestion(text) {
    setSearchQuery(text);
    runSearch(text);
  }

  if (loading) {
    return <div className="app loading">Loading recommendation engine...</div>;
  }

  const displayProducts = searchMode ? searchResults : catalog;

  return (
    <div className="app">
      <header className="header">
        <h1>AI Product Recommendation Engine</h1>
        <p>
          Personalized picks via KNN + cosine similarity · Flask API · MongoDB
        </p>
        {stats?.product_count != null && (
          <p className="stats-line">
            Catalog: <strong>{stats.product_count}</strong> products
            {stats.database && (
              <>
                {' '}
                · Database: <strong>{stats.database}</strong>
              </>
            )}
          </p>
        )}
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
          onSubmit={runSearch}
          onClear={clearSearch}
          searching={searching}
          suggestions={suggestions}
          onPickSuggestion={handlePickSuggestion}
        />
        {!searchMode && (
          <div className="quick-searches">
            <span className="quick-label">Try:</span>
            {POPULAR_SEARCHES.map((term) => (
              <button
                key={term}
                type="button"
                className="chip"
                onClick={() => handlePickSuggestion(term)}
              >
                {term}
              </button>
            ))}
          </div>
        )}
      </header>

      <Toast message={toast} onDismiss={() => setToast('')} />
      {error && <div className="error">{error}</div>}

      {searchMode && (
        <section className="section search-results-section">
          <h2 className="section-title">
            Search results
            <span className="badge">{searching ? '…' : `${searchResults.length} found`}</span>
          </h2>
          <p className="section-hint">
            Showing matches for <strong>&ldquo;{activeSearch}&rdquo;</strong> — ranked by relevance
            (name, category, description, tags).
          </p>
          {searching ? (
            <p className="empty">Searching catalog…</p>
          ) : searchResults.length === 0 ? (
            <div className="empty-panel">
              <p className="empty">No products matched your search.</p>
              <p className="empty-sub">Try a shorter term or pick a suggestion below.</p>
              <div className="quick-searches">
                {POPULAR_SEARCHES.map((term) => (
                  <button
                    key={term}
                    type="button"
                    className="chip"
                    onClick={() => handlePickSuggestion(term)}
                  >
                    {term}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="grid">
              {searchResults.map((p) => (
                <ProductCard
                  key={p.id}
                  product={p}
                  showRelevance
                  selected={selectedProduct?.id === p.id}
                  onSelect={handleSelectProduct}
                  onLike={handleLike}
                />
              ))}
            </div>
          )}
        </section>
      )}

      {!searchMode && (
        <section className="section">
          <h2 className="section-title">
            For You <span className="badge">KNN + user profile</span>
          </h2>
          {recommendations.length === 0 ? (
            <p className="empty">No recommendations yet — like some products in the catalog below.</p>
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
      )}

      {selectedProduct && (
        <section className="section insights-panel">
          <h2 className="section-title">
            Similarity insights <span className="badge">cosine similarity</span>
          </h2>
          <h4>Selected: {selectedProduct.name}</h4>
          <p className="section-hint">
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
          {searchMode ? 'Full catalog' : 'Browse catalog'}{' '}
          <span className="badge">MongoDB + REST</span>
        </h2>
        {!searchMode && (
          <p className="section-hint">
            Search above to filter instantly. Click a product for similarity insights; like items to
            train your For You feed.
          </p>
        )}
        <div className="grid">
          {displayProducts.map((p) => (
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
