---
status: done
---

# `user-agent.mjs`: probe launches with inverted headless mode

`fetchUserAgent(browserType, headless)` must launch the probe in the
SAME mode the caller will use, because headless and headful Chromium
emit different default UAs. Negate `headless` in `launchOpts` and the
probe reads the wrong mode's UA; the cached value is then used by the
caller's launch — wrong UA on the wire.

The existing `fetchUserAgent pins probe to registry-resolved
executablePath` test inspected `opts.executablePath` only — it did not
observe `opts.headless`. Confirmed gap on first injection: bug passed
all 19 baseline tests.

## Injection

`src/user-agent.mjs`:

```diff
   const launchOpts = {
-    headless: headless,
+    headless: !headless,
     executablePath: registry
       .findExecutable(browserType.name())
       .executablePath(),
   };
```

## Test Coverage

`src/user-agent.test.mjs`: new test "fetchUserAgent passes headless
mode through to launch" — fixture captures `opts.headless` via
`onLaunch`, asserts the value matches both `true` and `false`
inputs. Mutation flips the captured value and the equality fails on
the first probe.
