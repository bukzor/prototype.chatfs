---
status: todo
---

# `capture.mjs`: origin storage cleared after `page.goto` instead of before

**Priority:** Medium-High. **Confidence:** Medium-High.

Prospective — targets `packages/har-browse/.claude/todo.kb/2026-07-22-
001-*.md`, not yet implemented. Ordering mutation: the clear call moves
below the `goto`. The app's boot script reads IndexedDB during startup —
in claude.ai's case from a document *inline script*, i.e. at parse time,
before any post-navigation CDP roundtrip can win the race. The cache is
read (hydration happens, no fetch), and only then wiped — so this
mutation additionally destroys the evidence, making the failure look
like a first-visit capture on every subsequent inspection.

## Injection

```diff
-  await clearStorage();
   await page.goto(url, { waitUntil: "commit" });
+  await clearStorage();
```

## Anticipated Test Coverage

Same hydrating fixture and assertion as
`clear-origin-storage-call-removed.md`, with one requirement on the
fixture: the read-IndexedDB-and-render-without-fetching decision must
happen in an inline script at document parse time (not deferred), so the
post-goto clear deterministically loses the race and the payload fetch
deterministically does not happen. Then the same
rWBS+RR-present-on-second-capture assertion kills this mutant.
