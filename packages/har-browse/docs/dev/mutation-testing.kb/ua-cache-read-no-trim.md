---
status: done
---

# `user-agent.mjs`: cache-file read missing `.trim()`

`readFileSync(cacheFile, "utf-8").trim()` — the trim defends against
hand-edited cache files with trailing whitespace/newlines (and is a
no-op for our own writes, which don't append `\n`). Drop the trim and
a stray newline propagates into the `User-Agent` request header,
which is a control character: undefined behavior; some endpoints
return 400, others log the whole header malformed.

## Injection

`src/user-agent.mjs` in `cachedUserAgent`:

```diff
-    return readFileSync(cacheFile, "utf-8").trim();
+    return readFileSync(cacheFile, "utf-8");
```

## Test Coverage

`src/user-agent.test.mjs` — "cachedUserAgent strips trailing
whitespace from cached UA" seeds the cache with `"TrailingNewline/1.0\n"`
and asserts the appended-SUFFIX result equals `"TrailingNewline/1.0 ${SUFFIX}"`.
Drop the `.trim()` and the assertion fails on the literal `\n` between
the seed and the SUFFIX.
