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

### Finalize (distinguish overlay-click vs window-close)

The two termination signals have different semantics and must be
distinguished (this is existing behavior in the toy script worth preserving):

- **Overlay click ("Done Capturing")** — user-declared success. Finalize
  HAR, log success message.
- **Window close** — user cancelled. Log "Cancelled by user" and exit.
  Any HAR bytes Playwright happened to flush are incidental; we do not
  advertise a HAR on this path.

```js
const DONE = "done";
const CANCEL = "cancel";

const outcome = await Promise.race([
  page.waitForFunction(
    () => document.getElementById("capture-done")?.dataset.clicked === "true",
  ).then(() => DONE).catch(() => CANCEL),
  context.waitForEvent("close").then(() => CANCEL),
]);

if (outcome === CANCEL) {
  console.error("Cancelled by user.");
  process.exit(2);
}

await context.close(); // flushes HAR
console.error(`HAR written to ${values.har}`);
```

Exit codes (per `cli-interface.md`, "exits 0 on success, nonzero on failure"):

- `0` — success (overlay click; HAR finalized)
- `2` — user cancelled (window closed); halts pipelines like
  `har-browse && toy_pluck.sh ...`
- `1` — reserved for genuine errors (Playwright throw, unwritable HAR
  path, etc.) via default uncaught-exception behavior

The `.catch(() => CANCEL)` handles Playwright's "has been closed" throw
when the page is torn down during `waitForFunction`; the
`context.waitForEvent("close")` catches the direct context-close signal
if it fires first.

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

The Agreed Design above is the spec. Steps here are file-level pointers
to where the edits land, not restatements of the behavior.

- [x] Rewrite `packages/har-browse/src/har_browse.mjs` per the Agreed
      Design sections (CLI, Profile path, Browser setup, Navigation,
      Finalize)
- [x] Update docs to reflect the new CLI and behavior:
  - `packages/har-browse/CLAUDE.md`
  - `packages/har-browse/README.md`
  - `packages/har-browse/design.kb/030-requirements.kb/cli-interface.md`
  - `packages/har-browse/design.kb/050-components.kb/toy-capture.md`
- [x] `pnpm --filter har-browse test` (test is self-contained; does not
      invoke `har_browse.mjs`, so it should still pass unchanged)

## Success Criteria

Externally observable outcomes. Code-level behavior lives in the Agreed
Design above and is verified by reading the Finalize section.

- [ ] `har-browse https://chatgpt.com/` opens real Chrome; first run
      prompts login; subsequent runs with the same `--profile` skip it
- [ ] Profile dir exists at
      `${XDG_CACHE_HOME:-$HOME/.cache}/har-browse/profile/default_profile`
      after first run
- [ ] HAR contains all network activity visible in Chrome DevTools for
      the session
- [ ] `pnpm --filter har-browse test` passes

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
