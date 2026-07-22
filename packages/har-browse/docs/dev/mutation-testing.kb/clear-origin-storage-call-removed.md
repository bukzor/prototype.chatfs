---
status: todo
---

# `capture.mjs`: `Storage.clearDataForOrigin` call removed (option silently ignored)

**Priority:** High. **Confidence:** High.

Prospective — targets `packages/har-browse/.claude/todo.kb/2026-07-22-
001-claude-ai-revisits-render-from-persisted-React-Query-IndexedDB-
cache--so-capture-sees-no-conversation-traffic.md`, not yet implemented.
If `startCapture` accepts `clearOriginStorage: true` but the CDP call is
deleted (or the option never wired through), the revisit-hydration
failure mode returns exactly: the app boots on its persisted IndexedDB
cache, never fetches the payload, and the capture is silently empty of
conversation traffic while appearing successful. This is the verified
root cause of the 2026-07-22 a59dc891 zero-events run — the whole point
of the feature.

## Injection

```diff
   const page = context.pages()[0] ?? (await context.newPage());
   const { events, done } = await attachCapture(page, { howto });
-  if (clearOriginStorage) {
-    const session = await context.newCDPSession(page);
-    await session.send("Storage.clearDataForOrigin", {
-      origin: new URL(url).origin,
-      storageTypes: "indexeddb",
-    });
-  }
   await page.goto(url, { waitUntil: "commit" });
```

## Anticipated Test Coverage

Needs a hydrating fixture: a toy-server page whose script, on first
load, fetches `/api/payload` and writes it to IndexedDB; on subsequent
loads, if the IndexedDB entry exists, renders from it *without*
fetching. Test: capture once (populates IndexedDB in the persistent
profile), then capture again with `clearOriginStorage: true` and assert
the second capture's stream contains `Network.requestWillBeSent` +
`Network.responseReceived` (with body) for `/api/payload`. With this
mutation injected, the second capture has zero payload events — the
faithful miniature of the claude.ai symptom.
