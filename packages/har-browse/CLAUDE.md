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
- `src/` — Playwright HAR recorder with injected "Done" button
  - `har_browse.mjs` — Launches persistent-context browser, records HAR, waits
    for the human to click "Done" (exit 0) or close the window (exit 2).
    Per-profile state persists under
    `${XDG_CACHE_HOME:-$HOME/.cache}/har-browse/profile/${profile}`.
- `toy_pluck.sh` — jq filter: extracts /api/conversation from HAR (stdin → stdout)
- `out.har` — Example HAR output (gitignored)

## Design Knowledge

- `design.kb/` — Structured KB collections (010-mission through 060-deliverables)
- `data/todo-llmfs.chatgpt.com.splat/extracted/01-toy-playwright-spec.md` — Original design artifact
