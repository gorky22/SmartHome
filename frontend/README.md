# SmartHome React Frontend

This is a minimal React + Vite frontend that calls the backend API under `/api` (Vite dev server proxies `/api` → `http://localhost:8000`).

Quick start

```bash
cd frontend
npm install
npm run dev
```

Then open the printed dev URL (http://localhost:5173 by default). The app will request from `/api/devices` and related endpoints which will be proxied to the backend.

If you want the frontend served from the backend (single origin) I can add static file serving on the backend side.

# SmartHome Frontend (simple demo)

This is a minimal single-page app (vanilla JS + Chart.js) used to demo the backend API.

How to use

1. Serve this folder (e.g. `python -m http.server 8080` from the `frontend/` folder).
2. Make sure your backend is running at `http://localhost:8000` or set `window.API_BASE` in the console or replace the `API_BASE` in `app.js`.
3. Open `http://localhost:8080` in your browser.

Features

- Lists devices
- Click device to list sensors
- Click sensor to view logs (table) + interactive Chart.js chart and stats
- Date range filter
