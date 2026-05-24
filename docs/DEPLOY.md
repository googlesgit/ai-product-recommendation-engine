# Deploy: GitHub Pages (frontend) + Render (API) + Atlas (database)

GitHub Pages hosts **only the React UI** (static files). Flask and MongoDB run elsewhere.

| Piece | Host | URL |
|-------|------|-----|
| Frontend | GitHub Pages | `https://googlesgit.github.io/ai-product-recommendation-engine/` |
| API | Render (free) | `https://YOUR-SERVICE.onrender.com/api` |
| Database | MongoDB Atlas (free) | connection string in Render env |

---

## Step 1 — MongoDB Atlas (5–10 min)

1. Go to [mongodb.com/atlas](https://www.mongodb.com/atlas) → create free cluster.
2. **Database Access** → add user + password.
3. **Network Access** → **Allow access from anywhere** (`0.0.0.0/0`) for demos.
4. **Connect** → **Drivers** → copy connection string, e.g.  
   `mongodb+srv://USER:PASS@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority`
5. Append database name:  
   `mongodb+srv://USER:PASS@cluster0.xxxxx.mongodb.net/recommendations?retryWrites=true&w=majority`

---

## Step 2 — Render API (5–10 min)

1. Push this repo to GitHub (if not already).
2. [dashboard.render.com](https://dashboard.render.com) → **New** → **Blueprint** → connect `googlesgit/ai-product-recommendation-engine`.
3. When prompted, set **`MONGO_URI`** to your Atlas string from Step 1.
4. Deploy. Note your service URL, e.g. `https://ai-product-recommendation-api.onrender.com`.
5. Test: open `https://YOUR-SERVICE.onrender.com/api/health` — should show `"database": "connected"` and `"product_count": 48` (auto-seed on first start).

**Cold start:** Free Render sleeps after ~15 min idle; first request may take 30–60 seconds.

---

## Step 3 — GitHub Pages (frontend)

### A. Enable Pages (one time)

1. Repo → **Settings** → **Pages**.
2. **Build and deployment** → Source: **GitHub Actions** (not “Deploy from branch”).

### B. Point frontend at your API

1. Repo → **Settings** → **Secrets and variables** → **Actions** → **Variables** tab.
2. **New repository variable**
   - Name: `VITE_API_URL`
   - Value: `https://YOUR-SERVICE.onrender.com/api` (include `/api`, no trailing slash)

### C. Deploy

Push to `main` or run **Actions** → **Deploy frontend to GitHub Pages** → **Run workflow**.

After ~2 minutes, open:

**https://googlesgit.github.io/ai-product-recommendation-engine/**

---

## Step 4 — Load products (seed database)

Render **free plan has no Shell**, so use one of these:

### Option A — Browser (after `/api/seed` is deployed)

Open once in your browser:

```text
https://ai-product-recommendation-api.onrender.com/api/seed
```

You should see JSON like `"product_count": 48`. Then check `/api/health`.

### Option B — curl (same)

```bash
curl -X POST https://ai-product-recommendation-api.onrender.com/api/seed
```

### Option C — From your Mac (works immediately, no redeploy)

```bash
cd backend
export MONGO_URI="mongodb+srv://USER:PASSWORD@cluster0.tkmieck.mongodb.net/recommendations?retryWrites=true&w=majority"
export MONGO_DB=recommendations
python3 scripts/seed_data.py
```

Push the latest code first if `/api/seed` returns 404.

### Re-seed later (reset catalog)

Run Option C again, or drop collections in Atlas Data Explorer, then hit `/api/seed` again.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Pages shows README only | Pages source must be **GitHub Actions**, not branch `/root` |
| UI loads but “API error” | Set `VITE_API_URL` variable; re-run deploy workflow |
| Blank page / 404 on refresh | Workflow copies `404.html` for SPA routing — redeploy |
| API slow first load | Render free tier cold start — wait and retry |
| CORS errors | API already allows `*` on `/api/*` — check `VITE_API_URL` ends with `/api` |
| `SSL handshake failed` / `TLSV1_ALERT_INTERNAL_ERROR` on Render | Atlas **Network Access** → `0.0.0.0/0`; ensure latest code uses `certifi` in `database.py`; redeploy |

---

## Local vs production

| | Local (Docker) | Production |
|--|----------------|------------|
| Frontend | `http://localhost:3000` | GitHub Pages URL |
| API | `http://localhost:5001/api` | Render URL + `/api` |
| `VITE_API_URL` | not needed | set in GitHub Actions variable |
