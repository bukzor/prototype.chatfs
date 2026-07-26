---
status: done
---

# `capture.mjs`: `Network.setBypassServiceWorker` not applied to the session

**Priority:** High. **Confidence:** High.

A service worker with a cache-first handler answers the page's payload
fetch out of Cache Storage, so nothing crosses the network and the
per-page CDP session sees nothing — the never-requested gap of
`.claude/todo.kb/2026-07-23-001-*`, reached without any of that todo's
non-page-target machinery. Bypassing is the interim mitigation: it
converts service-worker-mediated traffic into ordinary page-session
events, at the cost of leaving the page uncontrolled.

## Injection

`src/capture.mjs`, in `wireSession`:

```diff
     await session.send("Network.setCacheDisabled", { cacheDisabled: true });
-    await session.send("Network.setBypassServiceWorker", { bypass: true });
     await session.send("Page.enable");
```

## Test Coverage

`tests/session_settings.spec.mjs`: "service-worker-mediated payload
still crosses the network" — the `/sw-page` + `/sw.js` fixture
registers a cache-first worker for `/payload?id=sw` and loads three
times. Three loads, not two: the first only registers the worker (its
`clients.claim()` may or may not land before that load's fetch), the
second is controlled from the start and would populate the worker's
cache, and the third is the load a cache-first worker could answer
entirely off-network. The oracle is the server's `requestLog`: all
three fetches must reach it. Confirmed red under injection at exactly
that assertion (2 of 3).

The page also reports `navigator.serviceWorker.controller` into
`#content`, asserted `false` — bypassing leaves the page uncontrolled,
which is the mechanism behind the network-fetch count and the reason a
fixture cannot wait for a controller before fetching.

## Live Status

Unvalidated against any live provider. The 2026-07-26 claude.ai
verification (devlog `2026-07-26-002`) found no `fromServiceWorker` responses in any capture,
and a run carrying this setting still recorded zero conversation
traffic -- so this setting is not what fixes
`.claude/todo.kb/2026-07-22-001-*`, and must not be described as
covering it. The coverage above is fixture-level only.
