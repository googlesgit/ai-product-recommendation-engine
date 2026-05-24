import { useCallback, useEffect, useState } from 'react';
import ProductCard from './components/ProductCard';
import SearchBar from './components/SearchBar';
import Toast from './components/Toast';
import { useDebouncedValue } from './hooks/useDebouncedValue';
import { api } from './services/api';
import { clearSession, getSessionId } from './services/session';

const POPULAR_SEARCHES = ['iphone', 'headphones', 'microwave', 'yoga', 'books', 'electronics'];

export default function App() {
  const [sessionId] = useState(() => getSessionId());
  const [sessionStats, setSessionStats] = useState({ likes: 0, views: 0 });
  const [profileMode, setProfileMode] = useState('session');
  const [demoUsers, setDemoUsers] = useState([]);
  const [demoUserId, setDemoUserId] = useState('user_1');
  const [catalog, setCatalog] = useState([]);
  const [categories, setCategories] = useState([]);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [catalogPage, setCatalogPage] = useState(1);
  const [catalogTotal, setCatalogTotal] = useState(0);
  const [catalogPages, setCatalogPages] = useState(1);
  const [catalogLoadingMore, setCatalogLoadingMore] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [activeSearch, setActiveSearch] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [searchMessage, setSearchMessage] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [recentViews, setRecentViews] = useState([]);
  const [similar, setSimilar] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState('');
  const [stats, setStats] = useState(null);

  const activeUserId = profileMode === 'demo' ? demoUserId : sessionId;
  const debouncedQuery = useDebouncedValue(searchQuery, 450);
  const searchMode = activeSearch.trim().length > 0;

  const refreshSessionStats = useCallback(async () => {
    const data = await api.getSession();
    setSessionStats(data.stats || { likes: 0, views: 0 });
  }, []);

  const loadRecommendations = useCallback(async (userId) => {
    const data = await api.getRecommendations(userId);
    setRecommendations(data.recommendations || []);
  }, []);

  const loadRecentViews = useCallback(async (userId) => {
    const data = await api.getRecentViews(userId);
    setRecentViews(data.products || []);
  }, []);

  const loadSimilar = useCallback(async (productId) => {
    if (!productId) return;
    const data = await api.getSimilar(productId, 5);
    setSimilar(data.similar_products || []);
  }, []);

  const loadCatalog = useCallback(async (page = 1, { append = false, category = '' } = {}) => {
    const data = await api.getProducts({ page, limit: 24, category });
    setCatalogPage(data.page || page);
    setCatalogTotal(data.total ?? 0);
    setCatalogPages(data.pages ?? 1);
    setCatalog((prev) => (append ? [...prev, ...(data.products || [])] : data.products || []));
    return data;
  }, []);

  const runSearch = useCallback(async (query) => {
    const q = query.trim();
    setActiveSearch(q);
    if (!q) {
      setSearchResults([]);
      setSearchMessage('');
      setSearching(false);
      return;
    }
    try {
      setSearching(true);
      setError(null);
      const data = await api.searchProducts(q);
      setSearchResults(data.products || []);
      setSearchMessage(data.message || '');
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
    setSearchMessage('');
    setSuggestions([]);
  }, []);

  useEffect(() => {
    async function init() {
      try {
        setLoading(true);
        setError(null);
        const health = await api.health();
        setStats(health);
        await api.bootstrapSession();
        await refreshSessionStats();
        const [demoRes, categoriesRes] = await Promise.all([
          api.getDemoUsers(),
          api.getCategories(),
        ]);
        setDemoUsers(demoRes.users || []);
        if (demoRes.users?.length) {
          setDemoUserId(demoRes.users[0].id);
        }
        setCategories(categoriesRes.categories || []);
        await Promise.all([
          loadRecommendations(sessionId),
          loadRecentViews(sessionId),
        ]);
      } catch (e) {
        const hint = import.meta.env.VITE_API_URL
          ? ' Check that the API is up and CORS allows this origin.'
          : ' Set VITE_API_URL when building for production (see docs/DEPLOY.md). Locally: docker compose up.';
        setError(e.message + hint);
      } finally {
        setLoading(false);
      }
    }
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mount only
  }, []);

  useEffect(() => {
    if (loading) return;
    loadRecommendations(activeUserId).catch((e) => setError(e.message));
    if (profileMode === 'session') {
      loadRecentViews(activeUserId).catch(() => {});
    } else {
      setRecentViews([]);
    }
  }, [activeUserId, profileMode, loading, loadRecommendations, loadRecentViews]);

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
    if (loading || searchMode) return;
    loadCatalog(1, { category: categoryFilter }).catch((e) => setError(e.message));
  }, [categoryFilter, loading, searchMode, loadCatalog]);

  useEffect(() => {
    if (!toast) return;
    const id = setTimeout(() => setToast(''), 3200);
    return () => clearTimeout(id);
  }, [toast]);

  async function trackView(productId) {
    try {
      await api.recordInteraction(activeUserId, productId, 'view');
      if (profileMode === 'session') {
        await Promise.all([refreshSessionStats(), loadRecentViews(sessionId)]);
      }
    } catch {
      /* non-blocking */
    }
  }

  async function handleSelectProduct(product) {
    setSelectedProduct(product);
    trackView(product.id);
    try {
      await loadSimilar(product.id);
    } catch (e) {
      setError(e.message);
    }
  }

  async function handleLike(product) {
    try {
      const res = await api.likeProduct(activeUserId, product.id);
      await loadRecommendations(activeUserId);
      if (profileMode === 'session') {
        await refreshSessionStats();
      }
      setToast(
        res.duplicate
          ? `“${product.name}” is already in your likes`
          : `Added “${product.name}” to your likes — check For You above`
      );
    } catch (e) {
      setError(e.message);
    }
  }

  function handlePickSuggestion(text) {
    setSearchQuery(text);
    runSearch(text);
  }

  function switchToDemo(userId) {
    setProfileMode('demo');
    setDemoUserId(userId);
  }

  function switchToSession() {
    setProfileMode('session');
    setSelectedProduct(null);
    setSimilar([]);
  }

  function handleNewSession() {
    clearSession();
    window.location.reload();
  }

  async function handleLoadMore() {
    if (catalogPage >= catalogPages || catalogLoadingMore) return;
    try {
      setCatalogLoadingMore(true);
      await loadCatalog(catalogPage + 1, { append: true, category: categoryFilter });
    } catch (e) {
      setError(e.message);
    } finally {
      setCatalogLoadingMore(false);
    }
  }

  if (loading) {
    return <div className="app loading">Loading recommendation engine...</div>;
  }

  // Browse grid always uses paginated catalog; search results are a separate section
  const forYouHint =
    profileMode === 'session'
      ? sessionStats.likes > 0
        ? `Built from ${sessionStats.likes} like(s) in your session`
        : 'Like products below to build your taste profile'
      : 'Sample profile with pre-loaded likes';

  return (
    <div className="app">
      <header className="header">
        <h1>AI Product Recommendation Engine</h1>
        <p>
          Live catalog · hybrid recommendations (content + collaborative filtering)
        </p>
        {stats?.product_count != null && (
          <p className="stats-line">
            Catalog: <strong>{stats.product_count}</strong> products · Session:{' '}
            <strong title={sessionId}>{sessionId.slice(0, 14)}…</strong>
            {profileMode === 'session' && (
              <>
                {' '}
                · <strong>{sessionStats.likes}</strong> likes ·{' '}
                <strong>{sessionStats.views}</strong> views
              </>
            )}
          </p>
        )}

        <div className="profile-bar">
          {profileMode === 'session' ? (
            <>
              <span className="profile-pill active">Your profile</span>
              <button type="button" className="btn btn-outline btn-sm" onClick={handleNewSession}>
                New session
              </button>
            </>
          ) : (
            <button type="button" className="btn btn-outline btn-sm" onClick={switchToSession}>
              ← Back to your profile
            </button>
          )}
          <span className="profile-divider">|</span>
          <label htmlFor="demo-select" className="demo-label">
            Try sample:
          </label>
          <select
            id="demo-select"
            value={profileMode === 'demo' ? demoUserId : ''}
            onChange={(e) => {
              const v = e.target.value;
              if (v) switchToDemo(v);
              else switchToSession();
            }}
          >
            <option value="">—</option>
            {demoUsers.map((u) => (
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
            Matches for <strong>&ldquo;{activeSearch}&rdquo;</strong>
          </p>
          {searching ? (
            <p className="empty">Searching catalog…</p>
          ) : searchResults.length === 0 ? (
            <div className="empty-panel">
              <p className="empty">No products matched &ldquo;{activeSearch}&rdquo;.</p>
              <p className="empty-sub">
                {searchMessage ||
                  'We do not stock that item yet — try electronics, books, or a shorter term.'}
              </p>
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

      {!searchMode && profileMode === 'session' && recentViews.length > 0 && (
        <section className="section">
          <h2 className="section-title">
            Recently viewed <span className="badge">your activity</span>
          </h2>
          <div className="grid grid-compact">
            {recentViews.map((p) => (
              <ProductCard
                key={p.id}
                product={p}
                compact
                selected={selectedProduct?.id === p.id}
                onSelect={handleSelectProduct}
                onLike={handleLike}
              />
            ))}
          </div>
        </section>
      )}

      {!searchMode && (
        <section className="section">
          <h2 className="section-title">
            For You <span className="badge">hybrid ML</span>
          </h2>
          <p className="section-hint">{forYouHint}</p>
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
                  onLike={handleLike}
                />
              ))}
            </div>
          )}
        </section>
      )}

      {selectedProduct && (
        <section className="section insights-panel">
          <h2 className="section-title">
            Similar to &ldquo;{selectedProduct.name}&rdquo;
            <span className="badge">cosine similarity</span>
          </h2>
          <p className="section-hint">
            View recorded for your session. Ranked by feature-vector distance.
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
          <>
            <p className="section-hint">
              Click a product to record a <strong>view</strong> and see similar items. Use{' '}
              <strong>♥ Like</strong> to train For You.
            </p>
            {categories.length > 0 && (
              <div className="category-bar">
                <button
                  type="button"
                  className={`chip ${categoryFilter === '' ? 'active' : ''}`}
                  onClick={() => setCategoryFilter('')}
                >
                  All
                </button>
                {categories.map((c) => (
                  <button
                    key={c.slug}
                    type="button"
                    className={`chip ${categoryFilter === c.slug ? 'active' : ''}`}
                    onClick={() => setCategoryFilter(c.slug)}
                  >
                    {c.name}
                  </button>
                ))}
              </div>
            )}
          </>
        )}
        <div className="grid">
          {catalog.length === 0 && !searchMode ? (
            <p className="empty">Loading catalog…</p>
          ) : (
            catalog.map((p) => (
              <ProductCard
                key={p.id}
                product={p}
                selected={selectedProduct?.id === p.id}
                onSelect={handleSelectProduct}
                onLike={handleLike}
              />
            ))
          )}
        </div>
        {!searchMode && catalog.length > 0 && (
          <div className="catalog-footer">
            <span className="catalog-meta">
              Showing {catalog.length} of {catalogTotal} products
              {categoryFilter ? ` in ${categories.find((c) => c.slug === categoryFilter)?.name || categoryFilter}` : ''}
            </span>
            {catalogPage < catalogPages && (
              <button
                type="button"
                className="btn btn-outline"
                disabled={catalogLoadingMore}
                onClick={handleLoadMore}
              >
                {catalogLoadingMore ? 'Loading…' : 'Load more'}
              </button>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
