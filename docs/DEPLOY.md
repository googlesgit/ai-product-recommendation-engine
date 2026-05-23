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

## Step 4 — Re-seed production DB (optional)

If you need to reset catalog on Atlas:

```bash
# From your Mac, with MONGO_URI set to Atlas:
export MONGO_URI="mongodb+srv://..."
export MONGO_DB=recommendations
cd backend && python scripts/seed_data.py
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Pages shows README only | Pages source must be **GitHub Actions**, not branch `/root` |
| UI loads but “API error” | Set `VITE_API_URL` variable; re-run deploy workflow |
| Blank page / 404 on refresh | Workflow copies `404.html` for SPA routing — redeploy |
| API slow first load | Render free tier cold start — wait and retry |
| CORS errors | API already allows `*` on `/api/*` — check `VITE_API_URL` ends with `/api` |

---

## Local vs production

| | Local (Docker) | Production |
|--|----------------|------------|
| Frontend | `http://localhost:3000` | GitHub Pages URL |
| API | `http://localhost:5001/api` | Render URL + `/api` |
| `VITE_API_URL` | not needed | set in GitHub Actions variable |
