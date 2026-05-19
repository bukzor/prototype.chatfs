---
status: done
---

# `cache.mjs`: drop the `=`-in-key assertion

The hive encoding is `k=v/k=v/...`. A key containing `=` would parse
ambiguously (e.g. `a=b=c` could mean key `a` value `b=c` or key `a=b`
value `c`). The assertion is the only thing guaranteeing the encoding
is round-trippable. Without it, silent collisions between distinct
keys become possible.

## Injection

`src/cache.mjs`, in the `Object.entries(key).map(...)`:

```diff
-            assert(
-              !k.includes("="),
-              `cache key may not contain '=': ${JSON.stringify(k)}`,
-            );
```

## Test Coverage

`src/cache.test.mjs`: "cachePath rejects '=' in hive key (would parse
ambiguously)" — `assert.throws` against the exact error message.
