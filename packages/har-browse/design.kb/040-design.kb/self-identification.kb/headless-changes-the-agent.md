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

## Resolution: the capture is headful, and that is not an option

`brandUserAgent()` extends whatever `browser.userAgent()` returns, so a
headless run shipped `… HeadlessChrome/147.0.0.0 Safari/537.36` with our
field in the platform comment — disclosure intact, shape gate satisfied,
and `unblocked-sessions`' other half violated, since no human's browser
says `HeadlessChrome`.

The obvious repair was to normalize `HeadlessChrome` back to `Chrome`
under `--headless`. It was the wrong one, and the reason is worth
keeping: that would be the single place where we *hide* something rather
than add to it, adopted to preserve a mode nothing could ship. The
capture's cut is a human clicking Done; a headless capture has no
human, and never had a legitimate caller. Removing the mode subtracts a
problem instead of buying a lie to keep it.

So `har-browse --headless` is gone (2026-07-28) and `startCapture` no
longer takes `headless` — the production host launches headful, full
stop. The test-only `host_playwright.mjs` keeps its option: it misstates
nothing about production, and taking it away would put a window on the
developer's desktop for all 31 e2e specs to no purpose.

The payoff is in the test that could not previously do its job. While
`--headless` existed, `tests/user_agent_client_hints.spec.mjs` ran
headless, so its User-Agent assertion had to tolerate `HeadlessChrome/`
— it validated a string that would draw a challenge in production, and
could not have caught one that did. It now asserts ` Chrome/… Safari`
and the absence of `Headless`.

Cost: a handful of specs open real windows. Put the suite under a
virtual display (`xvfb-run pnpm test`) if that matters; the fix belongs
in how the suite is run, not in what the capture pretends to be.

## Re-measuring

The table came from a throwaway; if it needs re-deriving, launch each
combination against a `file:` page and read `navigator.userAgent` and
`navigator.userAgentData.brands`. The only subtlety is passing
`chromium.executablePath()` to puppeteer explicitly, so that the
comparison is against Playwright's *choice* of binary rather than
against a different install.
