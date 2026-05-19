---
status: done
---

# `cache.mjs`: `escape()` drops NUL-in-value assertion

`escape()`'s NUL guard is the only thing keeping a NUL byte from reaching
`mkdirSync` (which would reject on POSIX, or truncate the path on
malicious-input platforms). Defensive — the upstream key check covers
keys, but values flow through `escape()` only.

## Injection

`src/cache.mjs`, in `escape()`:

```diff
   const s = String(v);
-  assert(
-    !s.includes("\0"),
-    `filesystem paths may not contain NUL: ${JSON.stringify(s)}`,
-  );
   return s.replaceAll("/", "\\");
```

## Test Coverage

`src/cache.test.mjs`: "cachePath rejects NUL in hive value" —
pre-existing `assert.throws` against the exact error message. Verified
on the inject→test→revert cycle: 1 fail with mutation, all-green
after revert.
