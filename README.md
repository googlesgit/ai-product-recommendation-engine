# AI-Powered Product Recommendation Engine

Full-stack recommendation system: **React** frontend, **Flask** REST API, **MongoDB**, **KNN + cosine similarity**, **Docker**.

## What you'll learn (maps to your resume)

| Resume bullet | Where in code | Interview answer |
|---------------|---------------|------------------|
| React + Flask REST | `frontend/`, `backend/routes/api.py` | Separation of concerns; frontend calls JSON APIs |
| Personalized recommendations | `GET /api/recommendations/user/<id>` | Hybrid: content (KNN + cosine) + item–item CF from co-likes |
| Search + similarity insights | `GET /api/products/search`, `GET /api/similar/<id>` | Cosine similarity ranks products by feature vectors |
| KNN + cosine similarity | `backend/models/recommender.py` | Cosine = angle between vectors; KNN = k nearest in that space |
| 25% accuracy improvement | `backend/scripts/evaluate_model.py` | Feature engineering (normalize price, category encoding, rating weight) vs raw features |
| MongoDB | `backend/services/database.py` | Products + user interactions stored as documents |
| Docker | `docker-compose.yml` | One command runs API, DB, UI |

## Architecture

```
Browser (React)  --HTTP-->  Flask API  --pymongo-->  MongoDB
                              |
                         recommender.py + collaborative.py
                         (KNN + cosine + co-like CF)
```

## Milestones A + C (catalog + hybrid ML)

- **Dynamic catalog** — syncs ~100 products from [DummyJSON](https://dummyjson.com/products) with images, brands, categories
- **Pagination & filters** — `GET /api/products?page=&limit=&category=`, category chips in UI
- **Hybrid For You** — 55% content similarity + 45% collaborative filtering from session/demo likes

## Phase 1 — Real sessions (live)

- **Anonymous session** per browser (`localStorage` + `X-Session-Id`)
- **Events**: `view` on product click, `like` on ♥ (stored in MongoDB with timestamps)
- **For You** built from **your** likes, not a fixed demo user
- **Recently viewed** from your session activity
- **Try sample** profiles optional (Alex / Jordan / Sam)

---

## Highlights (portfolio-ready)

- **Smart search** — multi-word queries (e.g. `micro oven` → microwave), relevance scoring, live debounced search, suggestions
- **Personalized For You** — hybrid content + collaborative filtering
- **Similarity panel** — cosine similarity on engineered features (price, category, rating, TF-IDF text)
- **Live catalog** — DummyJSON sync with product images; auto-loads when DB is empty
- **Polished UI** — search results section, quick-search chips, toast on like, catalog stats

## Live demo (GitHub Pages + Render)

| | URL |
|--|-----|
| **App (UI)** | https://googlesgit.github.io/ai-product-recommendation-engine/ |
| **Setup guide** | [docs/DEPLOY.md](docs/DEPLOY.md) |

GitHub Pages serves the React build. The Flask API runs on Render with MongoDB Atlas — follow **DEPLOY.md** once to connect everything.

---

## Quick start (local)

```bash
# From project root
docker compose up --build

# Sync catalog + demo personas (optional if DB already has data)
docker compose exec api python scripts/sync_catalog.py
docker compose exec api python scripts/seed_data.py

# Open app
open http://localhost:3000
```

> **Note:** The API auto-syncs from DummyJSON when the database is empty. If you still have an old hand-seeded catalog, run `sync_catalog.py` (add `drop_legacy=True` in code or `POST /api/catalog/sync?drop_legacy=true`).

**Without Docker** (local dev):

```bash
# Terminal 1: MongoDB (or use Docker only for mongo)
docker run -d -p 27017:27017 --name rec-mongo mongo:7

# Terminal 2: Backend
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export MONGO_URI=mongodb://localhost:27017
export MONGO_DB=recommendations
python scripts/sync_catalog.py
python scripts/seed_data.py
python app.py

# Terminal 3: Frontend
cd frontend && npm install && npm start
```

## API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Health check |
| GET/POST | `/api/seed` | One-time DummyJSON catalog load when DB is empty |
| POST | `/api/catalog/sync` | Refresh catalog from DummyJSON (`?drop_legacy=true` to remove old items) |
| GET | `/api/products/categories` | Category list for filters |
| GET | `/api/products?page=&limit=&category=` | Paginated catalog browse |
| GET/POST | `/api/session` | Register session; returns like/view counts |
| GET | `/api/interactions/recent` | Recently viewed products for a user/session |
| GET | `/api/users/demo` | Sample profiles only |
| GET | `/api/products` | List products (supports pagination + category filter) |
| GET | `/api/products/search?q=` | Smart search (multi-token + relevance score) |
| GET | `/api/products/search/suggestions?q=` | Search autocomplete hints |
| GET | `/api/products/<id>` | Product detail |
| GET | `/api/similar/<id>?k=5` | Similar products + cosine scores |
| GET | `/api/recommendations/user/<id>?k=8` | Hybrid personalized recommendations |
| POST | `/api/interactions` | Record like/view (`user_id`, `product_id`, `type`) |

## Run evaluation (25% metric story)

```bash
cd backend && python scripts/evaluate_model.py
```

Compares **baseline** features vs **engineered** features using Precision@K on held-out likes.

## Study guide — common interview questions

1. **Why cosine similarity instead of Euclidean distance?**  
   Cosine measures direction (taste profile), not magnitude. A user who rates everything high still has a meaningful preference vector.

2. **What is KNN here?**  
   We treat each product as a point in feature space. For a user profile vector, `KNeighborsClassifier` (or manual k-nearest) finds the k closest products not yet liked.

3. **What feature engineering did you do?**  
   See `recommender.py`: log-scaled price, one-hot category, normalized rating, review-count signal, description TF-IDF optional.

4. **Cold start?**  
   New users: show popular/high-rated (`GET /api/products?sort=rating`). New products: content-based similarity from features only.

5. **How did you measure 25%?**  
   Offline eval: hide 20% of each user's likes, recommend from the rest, measure Precision@5 before/after feature engineering.

## Project layout

```
backend/
  app.py                 # Flask entry
  models/recommender.py      # Content + hybrid ranker
  models/collaborative.py    # Item–item CF from likes
  routes/api.py              # REST routes
  services/database.py       # MongoDB
  scripts/sync_catalog.py    # DummyJSON catalog sync
  scripts/seed_data.py       # Demo user personas
frontend/
  src/App.jsx            # Main UI
  src/components/        # Cards, search, insights
```
