# Learning path — build this project step by step

Work through these sessions. After each, run the app and try the "Check yourself" questions out loud (interview style).

---

## Session 1: Big picture (30 min)

**Read:** `README.md` architecture diagram

**Concepts:**
- **Frontend** = UI in the browser (React)
- **Backend** = business logic + ML (Flask)
- **Database** = persistent storage (MongoDB)
- **REST API** = HTTP URLs that return JSON

**Check yourself:**
1. What is the difference between React and Flask in this project?
2. Why do we use MongoDB instead of storing products in a Python list?

---

## Session 2: Data layer (45 min)

**Read:** `backend/services/database.py`, `backend/scripts/seed_data.py`

**Do:**
```bash
# After MongoDB is running
cd backend && source venv/bin/activate
python scripts/seed_data.py
```

**Concepts:**
- A **document** in MongoDB ≈ one JSON object (one product, one interaction)
- **Collections** = tables: `products`, `interactions`, `users`
- Seeding = loading demo data so the app isn't empty

**Check yourself:**
1. What fields does each product document have?
2. How do we know user_1 "likes" electronics?

---

## Session 3: Machine learning core (60 min) — most important for interviews

**Read:** `backend/models/recommender.py` line by line

**Concepts:**

### Feature vector
Turn each product into numbers, e.g.:
`[log_price, rating/5, category_electronics=1, tfidf_word_headphones=0.3, ...]`

### Cosine similarity
Measures how similar two vectors point in the same direction.
- 1.0 = identical taste profile
- 0.0 = unrelated

Used in: **"Similar products"** when you click a item.

### KNN (K-Nearest Neighbors)
1. Build user profile = average of liked product vectors
2. Find K products closest to that profile (not already liked)

Used in: **"For You"** recommendations.

### Feature engineering (your 25% story)
**Baseline:** only price + rating → weak recommendations  
**Engineered:** log price, categories, review count, TF-IDF text → better Precision@K

**Do:**
```bash
python scripts/evaluate_model.py
```

**Check yourself:**
1. Explain cosine similarity without saying "it's a formula" — use "angle between taste vectors."
2. What happens for a brand-new user with zero likes?
3. How would you honestly describe the 25% number in an interview?

---

## Session 4: REST API (45 min)

**Read:** `backend/routes/api.py`, `backend/app.py`

**Try in browser or curl:**
```bash
curl http://localhost:5001/api/health
curl http://localhost:5001/api/products
curl "http://localhost:5001/api/recommendations/user/user_1"
```

**Concepts:**
- `@api_bp.route` maps URL → Python function
- `jsonify` returns JSON to the frontend
- CORS lets React (port 3000) call Flask (port 5001)

**Check yourself:**
1. What HTTP method is used when you click "Like"?
2. What does `refresh_recommender()` do after a new like?

---

## Session 5: React frontend (60 min)

**Read:** `frontend/src/App.jsx`, `frontend/src/services/api.js`

**Concepts:**
- `useState` = component memory (products list, selected user)
- `useEffect` = run code when page loads or user changes
- `fetch` via `api.js` = call Flask from browser

**Trace one flow:** Change user dropdown → `selectedUser` changes → `useEffect` → `loadRecommendations` → API → UI updates

**Check yourself:**
1. Where is the API base URL configured?
2. What happens when you click a product card?

---

## Session 6: Docker (30 min)

**Read:** `docker-compose.yml`

**Concepts:**
- **Image** = recipe (Python + dependencies)
- **Container** = running instance
- **Compose** = run mongo + api + frontend together

**Do:** `docker compose up --build` (requires Docker Desktop installed)

---

## Session 7: Git + resume (30 min)

```bash
cd ai-product-recommendation-engine
git init
git add .
git commit -m "Initial commit: AI product recommendation engine"
# Create repo on GitHub, then:
git remote add origin <your-url>
git push -u origin main
```

**Resume honesty:** You can now truthfully say you built this. For the 25% claim, say: *"On held-out likes, Precision@5 improved ~25% after feature engineering vs a price+rating baseline"* — run `evaluate_model.py` for your actual number.

---

## Top 10 interview questions (with answer outlines)

1. **Walk me through the architecture.** → React → Flask REST → MongoDB; ML in recommender.py  
2. **Content-based vs collaborative filtering?** → We use content-based (product features) + profile from user likes (hybrid-lite)  
3. **Why cosine not Euclidean?** → Scale-invariant preference direction  
4. **How do you handle cold start?** → Popular products by rating/reviews  
5. **How do you evaluate?** → Precision@K with held-out interactions  
6. **What is TF-IDF?** → Text importance; helps match "headphones" to "wireless audio"  
7. **Why Flask?** → Lightweight Python API; same language as sklearn pipeline  
8. **Why MongoDB?** → Flexible JSON documents for catalog + events  
9. **What would you add next?** → Real user auth, Redis cache, matrix factorization, A/B tests  
10. **Biggest challenge?** → Feature engineering and tuning K; measuring offline vs online metrics  
