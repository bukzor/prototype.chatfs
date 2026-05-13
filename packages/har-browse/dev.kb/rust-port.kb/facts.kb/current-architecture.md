# Current har-browse architecture

`packages/har-browse` is a Node/Playwright tool that drives a real Chromium browser, captures CDP events, and streams them as JSONL to stdout. The user terminates by clicking an injected "Done" button.

## Files

- `src/har_browse.mjs` — Entry point. Launches persistent-context browser, attaches capture, prints JSONL.
- `src/capture.mjs` — `captureEvents()` async generator. Attaches a CDP session per page, yields `{method, params}` objects matching the chrome-har wire format.
- `toy_server/` — Python `http.server` serving a fixed conversation fixture for testing.
- `toy_pluck.sh` — `jq` filter extracting the `/api/conversation` body from JSONL.

## Behavior

- **Output:** JSONL on stdout, one CDP event per line.
- **Termination:** Human clicks "Done" or closes the window.
- **Profile:** Persistent. Path: `${XDG_CACHE_HOME:-$HOME/.cache}/har-browse/profile/${profile}`. One per chatfs mount.
- **Response bodies:** Surface at `Network.responseReceived.params.response.body`, with `.encoding = "base64"` when applicable.

## Invariants (load-bearing)

Recent commits encoded subtle CDP-event-ordering invariants that define what "a complete capture" means. The Rust port must preserve them; their exact semantics live in the existing JS code and the commit messages:

- **BARRIER** — reentrant; merges into `barrier_consumed` state.
- **Causal watermark** — multi-witness, range-checked, body-integrity-checked.

These should be re-encoded as durable contract docs in `dev.kb/` (TBD `barrier-invariants.md`) at the time of commit `1000`. Port from existing code + tests, not from memory.
