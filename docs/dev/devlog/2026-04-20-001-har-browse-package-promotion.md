# 2026-04-20: har-browse package promotion

## Focus

Promote the `playwright-har-capture` incubator to a proper pnpm workspace
package (`packages/har-browse/`), rename the entry point to match the bin
name, and lock in the design for the real-site capture rewrite.

## What Happened

Two commits.

**`fd595fa` — `har-browse: promote incubator to package`**

- `git mv docs/dev/design-incubators/playwright-har-capture` →
  `packages/har-browse`
- Updated project-level refs in `CLAUDE.md`,
  `docs/dev/background.kb/har-format.md`
- Renamed `package.json` name field to `har-browse`

**`b4f72f4` — `har-browse: wire pnpm workspace, rename entry to match bin`**

- New `package.json` + `pnpm-workspace.yaml` at repo root
- `har-browse` declared as `devDependency` of root (`workspace:*`) —
  required for pnpm to link the bin into `node_modules/.bin/`
- `git mv packages/har-browse/toy_capture` → `src`
- `git mv packages/har-browse/src/capture.mjs` → `src/har_browse.mjs`
- Added `"bin": { "har-browse": "./src/har_browse.mjs" }`
- Updated 17 in-package references (README, CLAUDE.md, run.sh,
  deliverables/components/requirements kb)
- Verified: `pnpm --filter har-browse test` passes;
  `node_modules/.bin/har-browse` symlink exists

## Decisions

**Name: `har-browse`.** "Browse" is a human verb — signals interactive use,
unlike "capture" or "record" which are mode-agnostic. Forms a natural
command family (`har-browse`, `har-pluck`, `har-extract` later).

**Directory `src/`.** Conventional for package source; keeps overlay/test
files together with the entry point. Ruled out keeping `toy_capture/`
(misaligned now) and ruled out flat-at-package-root (would scatter the
overlay support files).

**File `har_browse.mjs` (underscore).** Matches repo convention
(`toy_capture/`, `test_persistent_injection.mjs`, `inject.mjs`). External
CLI name is hyphenated (`har-browse`) per Unix convention.

**pnpm workspace needed a root devDependency** on the package
(`workspace:*`) for pnpm to wire up the bin symlink. Without it, `pnpm
install` recognizes the workspace but doesn't link bins. Discovered
during verification.

## Design Locked (for next-session rewrite)

CLI: `har-browse [URL] [--har PATH] [--profile NAME] [--howto PATH]`

Three changes to `src/har_browse.mjs`:

- `launch()` + `newContext()` → `launchPersistentContext(profileDir, ...)`
- `waitUntil: 'networkidle'` → `waitUntil: 'commit'`
- Single `waitForFunction` → `Promise.race` against
  `context.waitForEvent('close')`

Profile path:
`${XDG_CACHE_HOME:-$HOME/.cache}/har-browse/profile/${profile:-default_profile}`.
No URL parsing. User-supplied profile name.

Full spec in
`.claude/todo.kb/2026-04-20-002-har-browse-implement-real-capture.md`.

## Next Session

Implement the rewrite per the locked design. Estimated ~30-50 line change
to one file plus doc updates (CLAUDE.md, README, cli-interface.md,
toy-capture.md component doc).

## Links

- [../../../.claude/todo.kb/2026-04-20-002-har-browse-implement-real-capture.md]
