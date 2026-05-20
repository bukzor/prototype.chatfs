---
status: done
---

# `user-agent.mjs`: `existsSync` check inverted

`if (existsSync(cacheFile)) return readFileSync(...)` — flip to
`!existsSync` and the cache logic inverts: first call (file absent)
returns garbage / throws ENOENT from the read; second call (file
present) re-launches Chromium to refetch. Effectively makes the
cache anti-functional.

## Injection

`src/user-agent.mjs`:

```diff
-  if (existsSync(cacheFile)) {
+  if (!existsSync(cacheFile)) {
     return readFileSync(cacheFile, "utf-8").trim();
   }
```

## Test Coverage

`src/user-agent.test.mjs` — all 3 tests seed the cache file then call
`userAgent(fakeChromium, ...)`. The inversion bypasses the seed,
falls through to `fetchUserAgent`, which calls `browserType.launch()`
on the fake and throws `browserType.launch is not a function`. Caught
without adding a test.
