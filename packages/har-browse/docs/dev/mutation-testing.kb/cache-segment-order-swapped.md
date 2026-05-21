---
status: done
---

# `cache.mjs`: ROOT/namespace/segments order swapped

`join(ROOT, namespace, segments)` puts the namespace immediately under
the cache root and lets each caller scope its keys. Reorder to
`join(ROOT, segments, namespace)` and unrelated callers share the
top-level `k=v/` segments — `browser` and (say) `extracted` end up
nested under `browser=chromium/...`. Cache collisions follow.

## Injection

`src/cache.mjs`, in `cachePath()`:

```diff
-  const path = join(ROOT, namespace, segments);
+  const path = join(ROOT, segments, namespace);
```

## Test Coverage

`src/cache.test.mjs` tests 1-4: all pin the exact path layout
`.../har-browse/<ns>/...`; swapping namespace and segments breaks every
equality assertion. UA tests are unaffected because both seed and
production use the same cachePath function and land at matching paths.
