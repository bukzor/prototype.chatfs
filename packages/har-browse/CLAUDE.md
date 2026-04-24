--- # workaround: anthropics/claude-code#13003
depends:
  - Skill(llm-kb)
---

# Playwright HAR Capture — Incubator

Cleanroom subproject: learn browser-driven HAR capture using Playwright against
a local-only toy app. Produces reusable components for the chatfs BB1 (capture)
pipeline.

## Key Files

- `toy_server/` — Python `http.server` serving static files on :8000
  - `api/conversation` — Fixed JSON fixture: 6-message tree with one fork
- `src/` — Playwright browser driver with injected "Done" button
  - `har_browse.mjs` — Launches persistent-context browser and streams CDP
    events as JSONL on stdout, one event per line. Terminates when the
    human clicks "Done" or closes the window. Per-profile state persists
    under `${XDG_CACHE_HOME:-$HOME/.cache}/har-browse/profile/${profile}`.
  - `capture.mjs` — `captureEvents()` async generator. Attaches a CDP
    session per page and yields events as `{method, params}` — the wire
    format `chrome-har` consumes. Response bodies land at
    `Network.responseReceived.params.response.body` (with
    `.encoding = "base64"` when applicable).
- `toy_pluck.sh` — jq filter: extracts /api/conversation body from the
  JSONL event stream (stdin → stdout)

## Design Knowledge

- `design.kb/` — Structured KB collections (010-mission through 060-deliverables)
- `data/todo-llmfs.chatgpt.com.splat/extracted/01-toy-playwright-spec.md` — Original design artifact
