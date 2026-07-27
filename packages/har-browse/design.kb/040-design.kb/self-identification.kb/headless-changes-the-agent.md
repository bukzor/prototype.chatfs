---
why:
  - unblocked-sessions
---

# Headless changes the agent

`--headless` is not a display choice the wire is unaware of. It rewrites
the User-Agent's browser product, and under one launcher it rewrites the
client-hint brand list too. A headless capture therefore announces
itself as automation on every request — an `unblocked-sessions`
violation that has nothing to do with our deliberate disclosure.

## Measured 2026-07-27

Same `chromium.executablePath()` passed to puppeteer; Playwright
launching itself. `file:` page, `navigator.userAgent` and
`navigator.userAgentData.brands` read directly.

| launcher | headless | UA product | `Sec-CH-UA` |
| --- | --- | --- | --- |
| puppeteer | yes | `HeadlessChrome/147.0.0.0` | `"Chromium";v="147", "Not.A/Brand";v="8"` |
| puppeteer | no | `Chrome/147.0.0.0` | `"Chromium";v="147", "Not.A/Brand";v="8"` |
| playwright | yes | `HeadlessChrome/147.0.7727.15` | `"HeadlessChrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"` |
| playwright | no | `Chrome/147.0.0.0` | `"Chromium";v="147", "Not.A/Brand";v="8"` |

Two separate effects, easily conflated:

- **Headless rewrites the UA product** under both launchers. This is
  Chromium's own behavior, not the launcher's.
- **Playwright headless is a different executable.** Its un-reduced
  version string (`147.0.7727.15` where Chromium's UA reduction gives
  everyone else `147.0.0.0`) marks it as `chromium_headless_shell`,
  which Playwright downloads separately and prefers when headless. It
  alone injects a `HeadlessChrome` *brand*. Puppeteer driving the
  headful binary with `--headless=new` leaves the brand list alone.

Headful, all four agree. The disagreement is entirely a headless
artifact.

## Consequences

`brandUserAgent()` extends whatever `browser.userAgent()` returns, so a
headless run ships `… HeadlessChrome/147.0.0.0 Safari/537.36` with our
field in the platform comment. The disclosure is intact and the shape
gate is satisfied; what is not satisfied is `unblocked-sessions`' other
half, since no human's browser says `HeadlessChrome`.

The CLI defaults to headful and the `har-browse --headless` flag exists
for tests and unattended runs, so nothing ships broken today. But the
flag is a foot-gun against a real provider, and the offline suite cannot
catch it: the suite runs headless, so its User-Agent assertions validate
a string that would draw a challenge in production.

Whether to normalize `HeadlessChrome` back to `Chrome` under `--headless`
is an open policy question, not an oversight. It pulls the requirement's
two halves against each other: suppressing it is the only way to be no
more suspicious than the same human uninstrumented, and it is also the
one place we would be *hiding* something rather than adding to it.
Tracked in `.claude/todo.md`.

## Re-measuring

The table came from a throwaway; if it needs re-deriving, launch each
combination against a `file:` page and read `navigator.userAgent` and
`navigator.userAgentData.brands`. The only subtlety is passing
`chromium.executablePath()` to puppeteer explicitly, so that the
comparison is against Playwright's *choice* of binary rather than
against a different install.
