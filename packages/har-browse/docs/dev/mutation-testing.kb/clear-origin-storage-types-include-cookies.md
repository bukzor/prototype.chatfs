---
status: done
---

# `capture.mjs`: `storageTypes` widened to include cookies (destroys login)

**Priority:** High. **Confidence:** High.

Targets `packages/har-browse/.claude/todo.kb/2026-07-22-
001-*.md`. The feature's constraint is asymmetric:
clear the app's data cache, preserve the session. If `storageTypes`
becomes `"all"` or grows `"cookies"`, every capture logs the user out of
the target site — for chatfs providers that means a manual re-login per
capture, which is exactly the cost the persistent-profile design exists
to avoid (`design.kb/030-requirements.kb/in-flow-termination.md` /
profile-per-mount). The capture stream itself looks *fine* (traffic
re-materializes even harder when logged out), so payload-presence
assertions can't catch this — it needs its own cookie-survival check.

## Injection

```diff
     await session.send("Storage.clearDataForOrigin", {
       origin: new URL(url).origin,
-      storageTypes: "indexeddb,cache_storage",
+      storageTypes: "all",
     });
```

## Test Coverage

`tests/clear_origin_storage.spec.mjs`: "clearOriginStorage preserves
cookies (login state)" — an expiring cookie is set on the target origin
in the first capture (a session cookie would not survive the browser
restart between captures), and after the second capture's clear the
cookie must still be listed by `context.cookies(url)` and must ride
along on the refetched payload request. That second check reads the
`Cookie` header off `Network.requestWillBeSentExtraInfo`, correlated by
`requestId`: plain `requestWillBeSent` reports renderer-side headers,
and the network service adds cookies after it. Confirmed red under
injection with `storageTypes: "all"`.
