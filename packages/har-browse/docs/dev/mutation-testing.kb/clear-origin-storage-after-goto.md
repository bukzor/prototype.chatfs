---
status: done
---

# `capture.mjs`: origin storage cleared after `page.goto` instead of before

**Priority:** Medium-High. **Confidence:** Medium-High.

Targets `packages/har-browse/.claude/todo.kb/2026-07-22-
001-*.md`. Ordering mutation: the clear call moves
below the `goto`. The app's boot script reads IndexedDB during startup —
in claude.ai's case from a document *inline script*, i.e. at parse time,
before any post-navigation CDP roundtrip can win the race. The cache is
read (hydration happens, no fetch), and only then wiped — so this
mutation additionally destroys the evidence, making the failure look
like a first-visit capture on every subsequent inspection.

## Injection

`src/capture.mjs`, in `startCapture` — the whole `if (clearOriginStorage)`
block moves below the navigation:

```diff
-  if (clearOriginStorage) { ...Storage.clearDataForOrigin... }
   await page.goto(url, { waitUntil: "commit" });
+  if (clearOriginStorage) { ...Storage.clearDataForOrigin... }
```

## Test Coverage

Killed by the same test as `clear-origin-storage-call-removed.md`. The
`/hydrate` fixture reads IndexedDB from an inline parse-time script, so
a clear issued after `page.goto` deterministically loses the race:
confirmed red under injection, with the revisit hydrating exactly as in
the call-removed case.
