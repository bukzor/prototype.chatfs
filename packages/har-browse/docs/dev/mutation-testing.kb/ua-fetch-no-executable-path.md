---
status: done
---

# `user-agent.mjs`: `executablePath` removed from probe launch

`launchOpts.executablePath` pins the probe to the same Chromium
revision the caller will launch (`registry.findExecutable(...)`).
Drop it and the probe launches Playwright's default-discovery
Chromium, which can be a different revision (especially with
`PLAYWRIGHT_BROWSERS_PATH` overrides). The UA cached under the
caller's revision key then doesn't match the browser the caller
actually launches — wrong UA emitted to remote endpoints.

## Injection

`src/user-agent.mjs`:

```diff
   const launchOpts = {
     headless: headless,
-    executablePath: registry
-      .findExecutable(browserType.name())
-      .executablePath(),
   };
```

## Test Coverage

`src/user-agent.test.mjs` — "fetchUserAgent pins probe to
registry-resolved executablePath" — uses a fake `browserType` that
records `launch()` opts and asserts `executablePath` equals
`registry.findExecutable("chromium").executablePath()`.
