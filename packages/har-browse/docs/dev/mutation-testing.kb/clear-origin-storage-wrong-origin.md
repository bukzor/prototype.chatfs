---
status: todo
---

# `capture.mjs`: clear targets the wrong origin (derived from the page, not the target URL)

**Priority:** Medium. **Confidence:** Medium-High.

Prospective — targets `packages/har-browse/.claude/todo.kb/2026-07-22-
001-*.md`, not yet implemented. The clear must run *before* navigation,
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
       storageTypes: "indexeddb",
     });
```

## Anticipated Test Coverage

Killed by the same second-capture payload-presence assertion as
`clear-origin-storage-call-removed.md` — wrong-origin clearing and
no clearing are observationally identical there (fixture origin's cache
survives, no refetch). No additional construction needed; note it in
that test's kill-list when confirming.
