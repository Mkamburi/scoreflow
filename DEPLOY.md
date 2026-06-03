# Deploying ScoreFlow

Use the same environment variable **names** as in `.env.example` files. Local `.env` files stay on your machine only.

## Render (backend)

1. Push this repo to GitHub.
2. In Render: **New → Blueprint** and connect the repo (uses root `render.yaml`).
3. In the dashboard, set **`CORS_ORIGINS`** to your frontend URL (e.g. `https://your-app.onrender.com`).
4. Do **not** use `scripts/install_basic_pitch.sh` on Render — that script is macOS-only (`../venv`, CoreML). The blueprint installs Basic Pitch via pip on Linux instead.
5. Use **`$PORT`** in the start command (already set in `render.yaml`), not a fixed `8000`.
6. Deploy the **frontend** separately (Vercel/Netlify) with `VITE_API_BASE_URL` pointing at your Render service URL.

**Note:** Demucs + Basic Pitch need a sizable instance; free tier may time out or run out of memory. Expect long first builds.

## Backend (FastAPI)

1. Deploy `backend/` (Python 3.12+, install `requirements.txt` + `scripts/install_basic_pitch.sh` on Mac/Python 3.13).
2. Set environment variables from `backend/.env.example`.
3. Use persistent disks or volumes for `UPLOAD_DIR`, `STEMS_DIR`, `MIDI_DIR` if the platform restarts containers.
4. Set `CORS_ORIGINS` to your real frontend URL(s), comma-separated.
5. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Optional: `OPENAI_API_KEY` only for GPT harmony experiments.

## Frontend (Vite + React)

1. Deploy `frontend/` (build: `npm ci && npm run build`).
2. Set `VITE_FLAT_APP_ID` and `VITE_API_BASE_URL` (your backend URL).
3. Allowlist the frontend domain in your Flat.io developer app.

## Local setup after clone

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# Edit .env files with your values
```
