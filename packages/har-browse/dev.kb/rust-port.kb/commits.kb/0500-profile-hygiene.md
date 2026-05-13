# Commit 0500: profile-hygiene

## What
Pre-launch hygiene: remove stale `SingletonLock`, seed `Default/Preferences`.

## Plan
- In `launch()` before spawn:
  - Remove `SingletonLock`, `SingletonCookie`, `SingletonSocket` if present.
  - If `Default/Preferences` is absent, write minimal JSON suppressing welcome tab + default-browser nag.

## Refs
- `../facts.kb/unknown-unknowns.md`
- `../facts.kb/threat-model.md`

## Outcomes
- [ ] Test: pre-create a `SingletonLock` in a profile dir, then `launch()` — succeeds
- [ ] Test: `launch()` twice sequentially on the same profile dir — both succeed
- [ ] Test: on a fresh profile dir, first page's title does not match Chrome's welcome page
- [ ] `Default/Preferences` exists in profile dir after first launch
