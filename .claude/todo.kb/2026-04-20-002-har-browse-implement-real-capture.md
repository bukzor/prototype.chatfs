<anthropic-skill-ownership llm-subtask />

---
required-reading:
  - packages/har-browse/CLAUDE.md
  - packages/har-browse/design.kb/030-requirements.kb/cli-interface.md
  - packages/har-browse/src/har_browse.mjs
---

# Implement har-browse real-site capture

**Priority:** High (blocks BB1 against real providers)
**Complexity:** Small (~30-50 line rewrite of one file + doc updates)
**Discovered:** 2026-04-20 session (see devlog)

## Problem Statement

`packages/har-browse/src/har_browse.mjs` currently targets the toy server
only. Three limitations block real-site use (chatgpt.com, claude.ai):

1. **No persistent login** — `chromium.launch()` + `newContext()` starts
   fresh every run. Real providers require login each time.
2. **`waitUntil: 'networkidle'`** — never fires on SPAs with SSE/websockets;
   also doesn't fire reliably on analytics-heavy sites.
3. **No `--profile` option** — can't separate state per target.

## Agreed Design (locked 2026-04-20)

### CLI

```
har-browse [URL] [--har PATH] [--profile NAME] [--howto PATH]
```

- Positional URL (no URL parsing logic inside the tool)
- `--profile NAME` — default `default_profile`
- `--har` and `--howto` unchanged

### Profile path

```
${XDG_CACHE_HOME:-$HOME/.cache}/har-browse/profile/${profile:-default_profile}
```

Static segments: `har-browse/profile/`. Variable segment: profile name
from flag. No URL-derived segments.

### Browser setup

Replace `chromium.launch()` + `context = browser.newContext(...)` with
`chromium.launchPersistentContext(profileDir, { ... })`:

```js
const context = await chromium.launchPersistentContext(profileDir, {
  headless: false,
  recordHar: { path: values.har, mode: "full" },
  viewport: null,
  ignoreDefaultArgs: ["--enable-unsafe-swiftshader"],
});
const page = context.pages()[0] ?? await context.newPage();
```

`launchPersistentContext` persists cookies, localStorage, service workers
across runs. First run: user logs in. Subsequent runs: already logged in.

Note: no separate `browser` handle. Replace `browser.close()` with
`context.close()` (which flushes the HAR).

### Navigation

```js
await page.goto(url, { waitUntil: 'commit' });
```

`commit` returns as soon as the response begins. Works on any site. HAR
recording is continuous regardless of `waitUntil` value.

### Finalize (race overlay-click vs window-close)

```js
await Promise.race([
  page.waitForFunction(() =>
    document.getElementById("capture-done")?.dataset.clicked === "true"),
  context.waitForEvent("close"),
]);
await context.close(); // idempotent; flushes HAR
```

Either signal finalizes the capture.

### Keep unchanged

- Overlay injection (`injectOverlay(page, { howto })`)
- `--howto` flag and overlay panel behavior
- Crostini workarounds (`viewport: null`, `ignoreDefaultArgs`)

## Known Gotchas

- **Cloudflare on chatgpt.com** may flag Playwright's bundled Chromium.
  Fallback: `channel: 'chrome'` to use system Chrome instead. Not needed
  unless it fails.
- **Google SSO** is sometimes touchier than site-native login forms.
- **HAR size** — real sessions produce MB-to-tens-of-MB HARs. Expected.
- **One profile per target site** — the user chose an explicit `--profile`
  flag rather than URL-derived paths. User's responsibility to pick
  distinct names for different sites (e.g. `--profile chatgpt`,
  `--profile claude`).

## Implementation Steps

- [ ] Add `--profile` option to `parseArgs` (default `"default_profile"`)
- [ ] Import `os`, `path` (node built-ins); compute `profileDir`
- [ ] Replace `chromium.launch(...)` + `browser.newContext(...)` with
      `chromium.launchPersistentContext(profileDir, {...})`
- [ ] Drop the separate `browser` variable; use `context` directly
- [ ] Get `page` via `context.pages()[0] ?? await context.newPage()`
- [ ] Change `waitUntil` from `'networkidle'` to `'commit'`
- [ ] Replace the single `waitForFunction` with `Promise.race([...])`
- [ ] Replace `browser.close()` with `context.close()` (single close)
- [ ] Update `packages/har-browse/CLAUDE.md`, `README.md`,
      `design.kb/030-requirements.kb/cli-interface.md`,
      `design.kb/050-components.kb/toy-capture.md` to reflect new CLI
      and behavior
- [ ] Run `pnpm --filter har-browse test` — should still pass (toy
      server uses `networkidle` internally in the test, which works
      against static files; test doesn't invoke har_browse.mjs directly)
- [ ] Manual smoke: `pnpm exec har-browse https://example.com` — verify
      profile dir is created, browser launches, closing window flushes HAR

## Success Criteria

- [ ] `har-browse https://chatgpt.com/` opens a real browser, prompts
      for login on first run, skips login on subsequent runs with same
      `--profile`
- [ ] Closing the browser window produces a finalized HAR
- [ ] Clicking "Done Capturing" button also produces a finalized HAR
- [ ] HAR contains all network activity visible in Chrome DevTools
- [ ] Profile dir exists at
      `${XDG_CACHE_HOME:-$HOME/.cache}/har-browse/profile/default_profile`
- [ ] `pnpm --filter har-browse test` still passes

## Related Follow-ups (not blocking)

- Rename kb slug `toy-capture.md` → `har-browse.md`; update `why:` refs
  in `m1-har-capture.md`, `m2-capture-overlay.md` (cosmetic)
- Revisit `design.kb/010-mission.kb/har-capture-learning.md` — mission
  still framed as "learning"; refactor to reflect real package status
- `toy_pluck.sh` is hardcoded to `/api/conversation` — needs
  parameterization for real-site HARs (separate BB2 work)
- `packages/har-browse/node_modules/` and `pnpm-lock.yaml` (both
  gitignored) are leftover from the standalone incubator install;
  cleanup optional since root workspace install is authoritative now
