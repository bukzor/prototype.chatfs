# Devlog: 2026-08-14 — Startup flashes eliminated: session-restore forced off, UA probe backgrounded

## Focus

User-reported usability complaint: every `har-browse` launch flashed the
prior run's browser content, then a `file:///` listing, before landing
on the requested URL. Find the by-construction fix, not a timing
mitigation.

## Decisions

### `session.restore_on_startup` gets patched into the profile's `Preferences` before every launch

**Rationale:** Live-verified root cause, not guessed. A fresh profile,
closed gracefully via `browser.close()` (`profile.exit_type: "Normal"`,
no explicit `session.restore_on_startup` ever written), still restored
its prior tab on the next `startCapture` launch. Opening
`chrome://settings/onStartup` on the actual `default_profile` in a live
run (human-driven, at the user's request) showed "Continue where you
left off" selected despite nobody choosing it -- this unbranded
Chromium build's compiled-in default differs from what
`--hide-crash-restore-bubble` (a crash-recovery-infobar suppressor, a
separate code path) implied was already handled. Setting it to "Open
the New Tab page" writes `session.restore_on_startup: 5` (the value
Chromium itself wrote when the human flipped the radio button) --
confirmed to stop the restore by relaunching the same profile and
inspecting `browser.pages()` before any pruning runs.

New in `host_puppeteer.mjs`: `disableSessionRestore(profileDir)`, called
from `startCapture` right after `mkdirSync`. Patches rather than
overwrites -- reads the existing JSON (or starts from `{}` on a
profile's first-ever launch), merges the one key, writes back.

**Alternatives considered:**
- *Navigate the reused tab to `about:blank` immediately, before the
  slower UA-probe/storage-clear setup.* Shrinks the exposure window but
  doesn't close it -- the OS paints the restored tab before any Node
  callback can react, an inherent race. Rejected once the settings
  panel showed an actual misconfigured default to fix instead of a
  timing budget to shrink.
- *Guess the Preferences schema from memory and ship it.* The
  numeric enum for `restore_on_startup` is undocumented and unstable
  across Chromium ages; guessing wrong would either no-op silently or
  break some other startup behavior. Every value used above
  (`exit_type`, `session.restore_on_startup`, the `5`) was read back out
  of an actual Chromium-written `Preferences` file first.

### UA-metadata probe page created with `background: true`

**Rationale:** `userAgentMetadata()`'s `browser.newPage()` call (which
navigates to `file:` for a secure-context `navigator.userAgentData`
read) was created in the foreground by default, per puppeteer's
`Target.createTarget` -- stealing window focus and flashing the
`file:///` root listing in front of the human mid-launch. `newPage`
takes a documented `background` option (`Browser.d.ts`); passing it
true keeps the probe off-screen. One-line fix, no protocol-level
uncertainty.

## Conventions Established

- When a Chromium startup/profile behavior is in question, don't
  reason from memory of Chrome's pref schema -- launch the actual pinned
  binary against a throwaway profile (`trash/`), force the state in
  question (kill it, close it, flip a setting), and read the
  `Preferences` JSON or `browser.pages()` back out. Memory of pref key
  names and their numeric enums is unreliable across Chromium versions
  and Chromium-vs-Chrome branding differences; the binary in
  `~/.cache/ms-playwright/` is ground truth and costs nothing to ask.

## Open Questions

None. This closes the "reused-profile tab restore" line from
`2026-07-26-003`'s Open Questions -- it no longer needs a spot in the
standing live `--howto` session.

## References

- `docs/dev/devlog/2026-07-26-003-puppeteer-core-host-migration-lands.md`
  -- Open Questions entry this closes ("A reused puppeteer profile
  session-restored the prior run's tabs...")
- `src/host_puppeteer.mjs` -- `disableSessionRestore`,
  `userAgentMetadata`
