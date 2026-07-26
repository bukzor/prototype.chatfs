---
status: done
---

# `capture.mjs`: `Storage.clearDataForOrigin` call removed (option silently ignored)

**Priority:** High. **Confidence:** High.

Targets `packages/har-browse/.claude/todo.kb/2026-07-22-
001-claude-ai-revisits-render-from-persisted-React-Query-IndexedDB-
cache--so-capture-sees-no-conversation-traffic.md`.
If `startCapture` accepts `clearOriginStorage: true` but the CDP call is
deleted (or the option never wired through), the revisit-hydration
failure mode returns exactly: the app boots on its persisted IndexedDB
cache, never fetches the payload, and the capture is silently empty of
conversation traffic while appearing successful. This is the verified
root cause of the 2026-07-22 a59dc891 zero-events run — the whole point
of the feature.

## Injection

`src/capture.mjs`, in `startCapture`:

```diff
   const page = context.pages()[0] ?? (await context.newPage());
   const { events, done } = await attachCapture(page, { howto, drainGraceMs });
-  if (clearOriginStorage) {
-    const session = await context.newCDPSession(page);
-    await session.send("Storage.clearDataForOrigin", {
-      origin: new URL(url).origin,
-      storageTypes: "indexeddb,cache_storage",
-    });
-    await session.detach();
-  }
   await page.goto(url, { waitUntil: "commit" });
```

## Test Coverage

`tests/clear_origin_storage.spec.mjs`: "clearOriginStorage forces a
revisit to refetch; payload body is captured" — the `/hydrate` fixture
in `tests/_common/server.mjs` is the miniature (first load fetches
`/payload?id=hydrate` and stores it in IndexedDB; later loads render
from the store without fetching). One capture populates the store, a
second capture of the same persistent profile runs with
`clearOriginStorage: true` and must see the payload's
`requestWillBeSent` plus a `responseReceived` carrying the body.
Confirmed red under injection: the revisit hydrates, and the payload
never crosses the network. "clearOriginStorage preserves cookies" fails
alongside it for the same reason.

The suite's third test, "fixture control: revisit hydrates from
IndexedDB with zero payload traffic", pins the fixture itself to the
symptom regime, so a fixture that quietly stopped hydrating couldn't
turn the kill assertion into a tautology.
