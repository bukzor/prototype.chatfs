---
status: done
---

# `capture.mjs`: `Network.setCacheDisabled` not applied to the session

**Priority:** Medium-High. **Confidence:** High.

Same failure class as the `clear-origin-storage-*` entries — a response
the page used that the capture never saw — one layer down. Without the
setting, a revisit's cacheable payload is answered from the HTTP cache:
no request reaches the server, and the events that do appear carry
`fromDiskCache`/`requestServedFromCache` with a body that is often no
longer fetchable via `Network.getResponseBody`. The capture looks
plausible and is missing payload.

## Injection

`src/capture.mjs`, in `wireSession`:

```diff
     await session.send("Network.enable");
-    await session.send("Network.setCacheDisabled", { cacheDisabled: true });
     await session.send("Network.setBypassServiceWorker", { bypass: true });
```

## Test Coverage

`tests/session_settings.spec.mjs`: "HTTP-cacheable payload is refetched
on revisit, not served from cache" — the `/cacheable` fixture endpoint
serves `cache-control: max-age=300`; the page fetches it, reloads, and
fetches again. The oracle is the server's `requestLog` (both fetches
must reach it), plus the absence of any
`Network.requestServedFromCache` event in the stream. Confirmed red
under injection: the second fetch is served from cache and never
reaches the server.

## Live Status

Unvalidated against any live provider. The 2026-07-26 claude.ai
verification (devlog `2026-07-26-002`) found no `Network.requestServedFromCache` in any capture,
and a run carrying this setting still recorded zero conversation
traffic -- so this setting is not what fixes
`.claude/todo.kb/2026-07-22-001-*`, and must not be described as
covering it. The coverage above is fixture-level only.
