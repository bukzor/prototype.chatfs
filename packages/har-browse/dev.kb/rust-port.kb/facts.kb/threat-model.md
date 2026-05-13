# Threat model (inherited constraint)

har-browse is **a browser first, a data-dumper second.** The port preserves this stance unchanged.

## Givens

- **Headed only.** No headless flows are currently needed or supported.
- **Human-in-the-loop termination.** User clicks the injected "Done" button.
- **Per-mount profile.** Each chatfs mount has its own browser-profile directory, isolating cookies, cache, login state. Sidesteps security/privacy/consent issues across mounts.
- **Authenticated capture.** User is logged in to the target site. Authentication is via session cookie (their own login), not automation evasion.
- **Non-adversarial.** Targets (claude.ai, chatgpt.com) gate on session, not on automation fingerprint. We do not need to evade bot detection.

## Consequences for the port

- No `navigator.webdriver` patching, no infobar suppression, no stealth plugins.
- Chrome-for-Testing builds are acceptable (no need for Playwright's custom Chromium patches).
- Profile-per-mount path scheme (`${XDG_CACHE_HOME}/har-browse/profile/${profile}`) ports verbatim — concurrent processes on distinct dirs do not contend (`SingletonLock` is per-dir).
