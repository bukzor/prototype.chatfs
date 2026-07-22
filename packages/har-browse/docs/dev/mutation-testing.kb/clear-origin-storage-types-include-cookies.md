---
status: todo
---

# `capture.mjs`: `storageTypes` widened to include cookies (destroys login)

**Priority:** High. **Confidence:** High.

Prospective — targets `packages/har-browse/.claude/todo.kb/2026-07-22-
001-*.md`, not yet implemented. The feature's constraint is asymmetric:
clear the app's data cache, preserve the session. If `storageTypes`
becomes `"all"` or grows `"cookies"`, every capture logs the user out of
the target site — for chatfs providers that means a manual re-login per
capture, which is exactly the cost the persistent-profile design exists
to avoid (`design.kb/030-requirements.kb/persistent-overlay.md` /
profile-per-mount). The capture stream itself looks *fine* (traffic
re-materializes even harder when logged out), so payload-presence
assertions can't catch this — it needs its own cookie-survival check.

## Injection

```diff
     await session.send("Storage.clearDataForOrigin", {
       origin: new URL(url).origin,
-      storageTypes: "indexeddb",
+      storageTypes: "all",
     });
```

## Anticipated Test Coverage

Set a cookie for the toy-server origin in the persistent profile (via a
prior capture whose fixture sets `Set-Cookie`, or `context.addCookies`
before attach), run a capture with `clearOriginStorage: true`, then
assert the cookie still exists (`context.cookies(url)` equality on
name/value) — and, belt-and-braces, that the fixture's
`/api/payload` request in the stream carries the `Cookie` header.
Deterministic, no timing.
