---
status: done
---

# `user-agent.mjs`: `browser.close()` dropped from probe finally

`fetchUserAgent` launches a throwaway Chromium just to read the
default UA via CDP. The `finally { await browser.close(); }` is what
tears it down. Drop the close and every UA probe (~once per
revision/headless combo, but also on cache miss) leaks a Chromium
process — eventually exhausts file descriptors / fights for the
profile lock.

## Injection

`src/user-agent.mjs`:

```diff
-  try {
-    const page = await browser.newPage();
-    const session = await page.context().newCDPSession(page);
-    const { userAgent } = await session.send("Browser.getVersion");
-    return userAgent;
-  } finally {
-    await browser.close();
-  }
+  const page = await browser.newPage();
+  const session = await page.context().newCDPSession(page);
+  const { userAgent } = await session.send("Browser.getVersion");
+  return userAgent;
```

## Test Coverage

`src/user-agent.test.mjs`:
- "fetchUserAgent closes the probe browser" — fake browser counts
  `close()` calls; asserts exactly 1.
- "fetchUserAgent closes the probe browser on error" — `try/finally`
  guarantee: throw inside body, assert close still fires.
