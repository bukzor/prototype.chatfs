# Risks Playwright silently handled

Cataloged risks Playwright handles transparently for us today. Mitigation cost in the Rust port is bounded.

## Mitigated by chromiumoxide

- **Target lifecycle / auto-attach.** Auto-handled (see `ecosystem-survey.md`). Two known iframe edge cases (#228, #280).
- **CDP transport.** WebSocket is fine at our scale; pipe-transport is an optimization, not a correctness concern.

## Mitigated by ~10 LOC of own code

- **`SingletonLock` cleanup.** Stale lock from a previous crash blocks subsequent launches on the same profile. Force-remove on launch.
- **First-run dialogs.** Welcome tab, default-browser nag, sync prompt. Pre-seed `Default/Preferences` JSON.
- **Process tree cleanup.** Chrome forks renderer/GPU/utility children. `setsid` on spawn + `killpg` on drop.
- **Stderr noise.** Chrome spams GPU errors, font warnings. Pipe stderr to a filter.
- **Crash phone-home.** `--disable-breakpad` flag suppresses minidump upload.

## Moot under our threat model

- **`navigator.webdriver` + automation infobar.** Highest-stakes Playwright magic in general — but our threat model (real browser, real user, authenticated capture) means we don't need to fight bot detection. See `threat-model.md`.

## Monitored at runtime, not mitigated up-front

Three risks are deferred to runtime assertions instead of pre-emptive code (see `../decisions.kb/assertion-strategy.md`):

- Vendored flag-list drift vs `chrome-launcher` upstream.
- Cross-origin iframe URL gap (chromiumoxide #280).
- Chrome version drift between CfT-managed binary and curated flag list applicability.
