---
why:
  - three-subsystem-pipeline
  - local-only-operation
---

# toy_server — Local Web App

Minimal HTTP server on `http://127.0.0.1:8000`.

## Endpoints

- `/` — HTML page that fetches `/api/conversation` on load
- `/api/conversation` — Fixed conversation graph (IDs, parents, branches)

## Responsibilities

- Serve deterministic JSON responses
- Provide a page with a fetchable endpoint (the capture script drives interaction)

## Implementation

`python3 -m http.server` serving static files. The `/api/conversation` endpoint
is a static JSON file at `api/conversation` (no extension).
