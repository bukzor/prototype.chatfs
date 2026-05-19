---
status: done
---

# `cache.mjs`: drop `{ recursive: true }` on `mkdirSync`

First-time access to a nested namespace (e.g. `cachePath("browser", {browser,revision,...})` with multi-segment hive key) crashes with ENOENT
because the intermediate directories don't exist yet. Cache becomes
fragile to fresh installs and to any namespace not previously created.

## Injection

`src/cache.mjs`:

```diff
-  mkdirSync(path, { recursive: true });
+  mkdirSync(path);
```

## Test Coverage

`src/cache.test.mjs`: any test that calls `cachePath` against a fresh
namespace (the first 3 happy-path tests do). Without recursive, the
intermediate `har-browse/<ns>/` dirs don't exist and `mkdirSync` throws
ENOENT before the test reaches its assertion.
