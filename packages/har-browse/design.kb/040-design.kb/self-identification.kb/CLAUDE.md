---
why:
  - unblocked-sessions
---

# Self-Identification

How har-browse tells a site what it is, and what providers do about it.

`unblocked-sessions` asks for two things at once: identify honestly, and
remain indistinguishable from a real browser in every way the site can
measure. They are compatible, but only in specific places — providers
gate on *where* a disclosure sits, not on what it says. That makes this
an empirical topic, not a matter of taste, and the measurements go stale
as providers change.

## What belongs here

- The disclosure channels available and what each one costs.
- Measured provider responses, with the date, the method, and enough
  detail to re-run.
- Variants ruled out, so the next author does not re-propose them.

## What does NOT belong

- Fingerprint-surface work that isn't disclosure (automation tells, TLS,
  `navigator.webdriver`) — those live with the launch flags that set them.
- The mechanics of applying an override → `src/host_puppeteer.mjs`.

## Re-measuring

`sbin/ua-gate-probe.mjs` is the instrument: it replays one real captured
request per variant from page context, control first. Update the tables
here in place with the new date rather than appending a second round —
a stale row that disagrees with a fresh one is worse than no row.
