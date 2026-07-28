---
why:
  - unblocked-sessions
---

# Headless changes the agent; windowless does not

Chromium's `--headless` is a *mode*, and it rewrites what the browser
says about itself — starting with the User-Agent's browser product.
`--ozone-platform=headless` is a display *backend*: it removes the
visible surface and nothing else. The distinction is the whole content
of this note, because one of them is unshippable and the other is what
we ship.

## Measured 2026-07-28

Sibling `headless-changes-the-agent.mjs`, same pinned Chromium
throughout, properties read from a `file:` page.

| launch | UA product | `Sec-CH-UA` | screen | GPU |
| --- | --- | --- | --- | --- |
| puppeteer headful (control) | `Chrome/147.0.0.0` | `Chromium, Not.A/Brand` | 1410x940 | virgl / Intel UHD |
| puppeteer, Chromium `--headless` | **`HeadlessChrome/…`** | `Chromium, Not.A/Brand` | **800x600** | **SwiftShader** |
| playwright `--headless` | **`HeadlessChrome/147.0.7727.15`** | **`HeadlessChrome, Not.A/Brand, Chromium`** | **800x600** | **SwiftShader** |
| windowless (what we ship) | `Chrome/147.0.0.0` | `Chromium, Not.A/Brand` | 1440x960 | virgl / Intel UHD |

`requestAnimationFrame` fires in all four — worth knowing, since the
Done-button predicate polls on it.

Chromium's headless mode carries three tells at once: the User-Agent
product, a stock 800x600 screen, and a software renderer in place of the
real GPU. Playwright's adds a fourth by running a different executable
entirely — `chromium_headless_shell`, betrayed by its un-reduced version
string — which injects a `HeadlessChrome` *brand* into the client hints.

The windowless row differs from the control in no property we know how
to check. `devicePixelRatio` is 1 rather than this machine's 1.6, and
the renderer reports desktop GL rather than GLES; both are ordinary
values a real browser reports, not anomalies.

## What we ship, and why it is called `--headless`

`har-browse --headless` and `startCapture({ windowless: true })` pass
three flags:

```
--ozone-platform=headless
--window-size=1280,900
--screen-info={0,0 1440x960}
```

The last two are load-bearing, not tuning. Without `--window-size` the
viewport is 0x0. Without `--screen-info` the `screen` object reports
1x1 — a value no real display has, and the only anomaly this
configuration would otherwise carry.

The CLI flag keeps the name users expect for "no window". The internal
option does not: `windowless` avoids colliding with puppeteer's
`headless`, which sits a few lines away in the same launch call and
means the thing we are avoiding. A future reader who "simplifies" one
into the other reintroduces every tell in the table above.

## History

`--headless` originally meant Chromium's mode. It was added 2026-07-26
so the suite would stop opening windows, removed 2026-07-28 once the
User-Agent consequence was measured, and reinstated the same day with
this definition.

The removal was right on its own terms: the mode could not ship, and
worse, the suite ran in it —
`tests/user_agent_client_hints.spec.mjs` had to tolerate
`HeadlessChrome/` in its assertion, so it validated a string that would
draw a challenge in production and could not have caught one that did.
Normalizing the string back to `Chrome` was rejected as the one place we
would hide something rather than add to it; the table above shows it
would also have been futile, since the GPU and screen would still have
given it away.

What changed is that the goal turned out to be reachable without the
mode. A windowless run is a real browser in every measurable sense,
purpose-built for the case where the correct human interaction is none —
so the suite is quiet *and* asserts ` Chrome/… Safari` with no
`Headless` anywhere.

## Consequence for the capture

Without a surface there is no Done button, so a windowless capture ends
only when its consumer closes the stream or the process dies. That is
the honest use: unattended runs and tests. A human-driven capture wants
the window, which is why headful remains the default everywhere.
