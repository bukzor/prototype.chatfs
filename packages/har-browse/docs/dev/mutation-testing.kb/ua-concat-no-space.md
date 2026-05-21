---
status: done
---

# `user-agent.mjs`: SUFFIX appended with no separating space

User-Agent product tokens are space-separated per RFC 7231. Drop the
space and `MockChrome/1.0har-browse/X.Y (+...)` becomes one fused
token — invalid UA syntax, fingerprints differently, and some endpoints
reject it.

## Injection

`src/user-agent.mjs`, in `userAgent()`:

```diff
-  return `${await cachedUserAgent(browserType, headless)} ${SUFFIX}`;
+  return `${await cachedUserAgent(browserType, headless)}${SUFFIX}`;
```

## Test Coverage

`src/user-agent.test.mjs` tests 8, 9, 10, 14 — equality assertions
expect `"<seed> ${SUFFIX}"` (with a separating space). Dropping the
space produces a fused token that fails equality.
