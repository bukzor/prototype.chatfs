---
status: done
---

# `capture.mjs`: profileDir mkdir not recursive in startCapture

`mkdirSync(profileDir, { recursive: true })` — the profile path
contains XDG-cache nested dirs (`har-browse/profile/<name>`) that may
not exist on a fresh machine. Drop the `recursive: true` and the
first launch with a non-existent parent fails with ENOENT before
Playwright is even reached. Distinct from `cache-no-recursive-mkdir`
which targets `cache.mjs`'s mkdir.

## Injection

`src/capture.mjs` in `startCapture`:

```diff
-  mkdirSync(profileDir, { recursive: true });
+  mkdirSync(profileDir);
```

## Test Coverage

`tests/start_capture.test.mjs` — "startCapture creates profileDir
recursively (parents missing)" — monkey-patches
`chromium.launchPersistentContext` and passes a nested profileDir whose
parents don't exist. Non-recursive mkdir ENOENTs before reaching the
fake launch; recursive mkdir creates parents and the fake's sentinel
throw propagates. Verified via `assert.rejects(..., /SENTINEL/)` plus
post-call `existsSync(profileDir)`.
