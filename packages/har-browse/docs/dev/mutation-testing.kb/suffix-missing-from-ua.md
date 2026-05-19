---
status: done
---

# `user-agent.mjs`: `userAgent()` doesn't append SUFFIX

The package's self-identifying suffix (`har-browse/<version>
(+homepage)`) is the contract with operators: they can grep their
access logs for it and reach the maintainer. Without it, traffic is
indistinguishable from vanilla headless Chromium.

## Injection

`src/user-agent.mjs`, in `userAgent()`:

```diff
-  return `${await cachedUserAgent(browserType, headless)} ${SUFFIX}`;
+  return await cachedUserAgent(browserType, headless);
```

## Test Coverage

`src/user-agent.test.mjs`: "userAgent appends `<name>/<version>
(+<homepage>)` SUFFIX to the cached UA" — seeds a known UA at the
production cache path (computed via the same `cachePath` hive key
production uses), then asserts exact equality against
`"<seeded> <SUFFIX>"`. Drop the SUFFIX and the trailing-space split
no longer matches.
