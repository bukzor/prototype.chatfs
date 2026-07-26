---
status: done
---

# `capture.mjs`: clear targets the wrong origin (derived from the page, not the target URL)

**Priority:** Medium. **Confidence:** Medium-High.

Targets `packages/har-browse/.claude/todo.kb/2026-07-22-
001-*.md`. The clear must run *before* navigation,
which means the page is still on `about:blank` (or a previous origin) —
so deriving the origin from the live page (`page.url()`,
`new URL(page.url()).origin`) instead of from the `url` argument clears
the wrong origin's storage (or errors on `about:blank`). The target
origin's IndexedDB survives intact and hydration proceeds; the option is
a no-op that looks implemented.

## Injection

```diff
     await session.send("Storage.clearDataForOrigin", {
-      origin: new URL(url).origin,
+      origin: new URL(page.url()).origin,
       storageTypes: "indexeddb,cache_storage",
     });
```

## Test Coverage

The predicted kill was wrong, and the reason matters: CDP answers a
`"null"` origin — which is what `about:blank` serializes to — by
clearing IndexedDB for *every* origin in the profile, not by erroring
or no-opping. So the mutant still clears the target's storage, the
revisit still refetches, and the payload-presence assertion passes.
Verified by probe: after a `"null"`-origin clear, a bystander origin's
IndexedDB was gone.

That makes the mutant an over-clear rather than an under-clear here,
though it is a true under-clear in production whenever the pre-goto
page holds a real URL (a restored tab) instead of `about:blank`. Either
way the defect is scope, so the test asserts scope:
`tests/clear_origin_storage.spec.mjs`, "clearOriginStorage is scoped to
the target origin" — a second `startServer()` on another port is
populated in the first capture, and after the second capture clears the
target origin, the bystander origin must still hydrate. Confirmed red
under injection.
