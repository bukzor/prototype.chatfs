---
status: done
---

# `user-agent.mjs`: cache key omits `headless`

Headful and headless Chromium emit different User-Agent strings
(headless mode used to advertise `HeadlessChrome` and may again).
Sharing a cached UA across modes means whichever mode populated the
cache first dictates the UA for both — defeating the whole point of
matching launch-mode UA.

## Injection

`src/user-agent.mjs`, in `cachedUserAgent()`:

```diff
   const cacheDir = cachePath("browser", {
     browser,
     revision,
     platform: platform(),
     arch: arch(),
-    headless: String(headless),
   });
```

## Test Coverage

`src/user-agent.test.mjs`: "cachedUserAgent cache key includes
headless mode" — seeds distinct UAs at `headless=true` and
`headless=false` paths, asserts each `userAgent(..., mode)` returns
its own seed. With the mutation, both calls land on the same cache
file and return the last-written value.
