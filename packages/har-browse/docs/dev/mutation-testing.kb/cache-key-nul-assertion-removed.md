---
status: done
---

# `cache.mjs`: drop the NUL-in-key assertion

The hive-key NUL guard is the only thing keeping a NUL byte in a key
from reaching `mkdirSync`. Distinct from the value-side guard in
`escape()` — keys are checked inside the `Object.entries(...).map`
closure, before `escape` runs. Drop it and a NUL in a key slips through
to `${escape(k)}=...`, then to the path.

## Injection

`src/cache.mjs`, in the `Object.entries(key).map(...)`:

```diff
-            assert(
-              !k.includes("\0"),
-              `cache key may not contain NUL: ${JSON.stringify(k)}`,
-            );
```

## Test Coverage

`src/cache.test.mjs`: "cachePath rejects NUL in hive key" — pre-existing
`assert.throws` against the exact error message. With the assert
removed, the throws check fails (mkdirSync would instead throw
ERR_INVALID_ARG_VALUE on the NUL, not the expected message).
