---
why:
  - ../../030-requirements.kb/undisrupted-operator-input.md
---

# Wayland window control is compositor-owned

Chrome runs as a native Wayland client in this dev environment
(Crostini via Sommelier), not under XWayland — confirmed by
`xwininfo -root -tree` finding no trace of it while a real window is
visibly open (only Sommelier's own stub windows appear). Wayland
deliberately keeps window placement and focus policy in the
compositor, not the client — a protocol design choice, not an
omission. Every technique below tried to reach around that from the
client side; all failed, live and human-verified.

## Measured 2026-08-14

| technique | goal | result |
| --- | --- | --- |
| `--window-position` launch flag | position off-screen | silently ignored |
| CDP `Browser.setWindowBounds` (position) | position off-screen | silently ignored — CDP acks success, window doesn't move |
| forced `--ozone-platform=x11` + `setWindowBounds` | position off-screen | still ignored (Crostini's XWayland doesn't help here either) |
| CDP `setWindowBounds({windowState: "minimized"})` | hide, then reveal | hides successfully, but **cannot be reversed** — `windowState: "normal"` afterward is a no-op |
| `--start-minimized` launch flag | start hidden | same as above: launches minimized, un-minimize doesn't work |
| CDP `Target.createTarget({background: true})` + `--no-startup-window` | avoid stealing OS keyboard focus on creation | window still received OS focus; keystrokes typed elsewhere landed in it |

The minimize finding has an external confirmation: the
[xdg-shell spec](https://wayland.app/protocols/xdg-shell) says of
`xdg_toplevel::set_minimized`, "There is no way to know if the surface
is currently minimized, nor is there any way to unset minimization on
this surface." That's not a Chromium gap, it's the protocol.

`Target.createTarget`'s `background` param is CDP's own purpose-built
mechanism for "create this target without stealing focus" — the most
targeted lever available — and it still didn't hold under this
compositor, when the backgrounded target is the browser's *first*
window (forced via `--no-startup-window`, so nothing else could have
grabbed focus first). This is not a contradiction of the same `background`
option's working use elsewhere in this codebase
(`userAgentMetadata()` in `src/host_puppeteer.mjs`, devlog
`2026-08-14-000`): that call backgrounds a *second* page inside a
browser that already has a foregrounded window — Chromium's own
tab-activation logic, which does honor `background`. A brand-new
toplevel surface's *initial* keyboard focus is the compositor's
decision, not Chromium's; only the second case is a lever a client
actually has.

## Consequence

There is no client-side lever, on this environment, for either "start
invisible" or "start without taking keyboard focus." A fix has to
avoid needing compositor cooperation — e.g. gating window creation
itself on an explicit operator action, so focus transfer only ever
follows something the operator just did on purpose.

## What did work (different problem)

An injected full-viewport DOM overlay (`evaluateOnNewDocument`, same
mechanism as the Done-button overlay) cleanly masks the page's real
content until removed, with no flash — proven live, twice, and proven
to not reappear on a second navigation once removed by identifier. That
fixes visual loading jank, not focus theft: a DOM overlay doesn't
change OS keyboard routing. See `070-future-work.kb/` if that's worth
picking up on its own.
