---
status: done
---

# `user-agent.mjs`: SUFFIX placed before the cached UA

Per the User-Agent convention this tool follows, the self-identifying
product token goes at the end so the browser's UA is what
fingerprinters see first. Reverse the order and our product token
leads — defeats UA-matching, surfaces this tool as the primary client.

## Injection

`src/user-agent.mjs`, in `userAgent()`:

```diff
-  return `${await cachedUserAgent(browserType, headless)} ${SUFFIX}`;
+  return `${SUFFIX} ${await cachedUserAgent(browserType, headless)}`;
```

## Test Coverage

`src/user-agent.test.mjs` tests 8, 9, 10, 14 — full-string equality
against `"<seed> ${SUFFIX}"` fails when the order is reversed
(`${SUFFIX} <seed>`).
