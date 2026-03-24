---
why:
  - three-subsystem-pipeline
  - local-only-operation
---

# toy_server — Local Web App

Minimal HTTP server on `http://127.0.0.1:8000`.

## Endpoints

- `/` — HTML page that fetches API endpoints on load
- `/api/ping` — `{"ok": true, "ts": "..."}`
- `/api/conversation` — Fixed conversation graph (IDs, parents, branches)
- `/api/large` — Larger JSON payload for size/streaming/compression testing

## Responsibilities

- Serve deterministic JSON responses
- Optionally apply gzip/brotli content encoding
- Provide a page with fetchable endpoints (the capture script drives interaction)

## Tech choice

Any of: Python FastAPI, Node Express, Rust axum. Pick whichever is fastest to
stand up. The server is disposable scaffolding.
