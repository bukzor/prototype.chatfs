---
status: done
---

# `user-agent.mjs`: cache key omits Chromium revision

The cached UA is bound to a specific Chromium build. When playwright
upgrades and the bundled Chromium revision changes, the cached UA
becomes stale and reports the *previous* Chromium version forever —
detectable as a tell by sites that fingerprint UA against the
TLS/JA3 stack.

## Injection

`src/user-agent.mjs`, in `cachedUserAgent()`:

```diff
   const cacheDir = cachePath("browser", {
     browser,
-    revision,
     platform: platform(),
     arch: arch(),
     headless: String(headless),
   });
```

## Test Coverage

`src/user-agent.test.mjs`: "cachedUserAgent cache key includes
Chromium revision" — seeds a sentinel UA at the path that *includes*
`revision=` and confirms `userAgent()` reads it. With the mutation,
production looks at a different path (no `revision=` segment), cache
misses, `fetchUserAgent` is invoked, and the returned UA doesn't match
the sentinel. The auxiliary `path.includes("revision=")` check fixes
the path-shape contract.
