# har-browse is an interactive, single-user tool

Frame har-browse's threat model as a *decision*, not a discovered
constraint:

**Decision:** har-browse operates as an interactive, single-user tool.
- Headed Chrome (no headless flows).
- Human terminates via the injected "Done" button.
- Per-mount profile (one browser profile per chatfs mount, under
  `${XDG_CACHE_HOME:-$HOME/.cache}/har-browse/profile/${profile}`).
- Authenticated via the user's own session cookie (no automation-style
  authentication, no token extraction).
- Targets are non-adversarial — services gate on session, not on
  automation fingerprint.

## Consequences

- **No bot-detection evasion.** No `navigator.webdriver` patching, no
  infobar suppression, no stealth plugins. The Chrome-for-Testing
  builds are acceptable as the binary; no need for Playwright's custom
  Chromium patches.
- **Profile-per-mount path scheme** ports verbatim to Rust;
  `SingletonLock` contention is per-directory and distinct directories
  don't contend.
- **No headless mode** is in scope for the Rust port (per
  `packages/har-browse/dev.kb/rust-port.md`).

## Why a decision, not a fact

har-browse *could* have been built as a headless / multi-user / token-
authenticated tool. It was chosen not to be. The choice produces the
constraints, not the other way around. Existing
`packages/har-browse/dev.kb/rust-port.kb/facts.kb/threat-model.md`
frames these as "givens" — a future restructure should rewrite the doc
as decision + consequences (deferred).

## Related

- Workspace policy:
  `docs/dev/technical-policy.kb/policy-safe-automation-boundary.md`
  (pending rename per
  `decision.kb/rename-safe-to-whitehat-automation-boundary.md`).
  That policy is the workspace-wide stance from which this single-
  package decision draws.

Decided 2026-05-21.
