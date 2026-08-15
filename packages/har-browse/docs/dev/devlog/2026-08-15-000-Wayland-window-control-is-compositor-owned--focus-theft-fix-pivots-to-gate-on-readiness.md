# Devlog: 2026-08-15 — Wayland window control is compositor-owned; focus-theft fix pivots to gate-on-readiness

## Focus

Started as a usability request: leave the launched window invisible
until content settles, instead of showing loading jank. User then
distrusted self-reported/CDP proof and required live human observation
before any conclusion or code change. Mid-session, the user corrected
the actual goal: not visual jank, but OS keyboard focus theft — a
newly launched, not-yet-ready `har-browse` window steals keystrokes the
operator is mid-typing elsewhere (this chat, a terminal). Everything
built before that correction (window-position hiding, minimize, splash
overlay) addressed the wrong problem.

## Decisions

### Every OS-level window-control lever is compositor-owned here, not client-controllable

**Rationale:** Live/human-verified, one technique at a time, each
against a full-viewport color page naming the expected state so there
was no ambiguity about what was actually seen:

- `--window-position` launch flag: silently ignored.
- CDP `Browser.setWindowBounds` (position): silently ignored — CDP
  acks success, the window never moves.
- Forcing `--ozone-platform=x11` + `setWindowBounds`: still ignored.
- CDP `setWindowBounds({windowState: "minimized"})`: hides
  successfully, but un-minimizing afterward is a no-op. Confirmed
  against the [xdg-shell spec](https://wayland.app/protocols/xdg-shell):
  "There is no way to know if the surface is currently minimized, nor
  is there any way to unset minimization on this surface." Not a
  Chromium gap — the protocol.
- `--start-minimized` launch flag: same as above.
- CDP `Target.createTarget({background: true})` combined with
  `--no-startup-window` (so the backgrounded target is the browser's
  *only* window, not a second one in an already-focused browser):
  still received OS keyboard focus. Confirmed by typing into the probe
  from outside the window and watching the characters land in its
  on-page readout.

Root cause: this dev environment (Crostini) runs Chrome as a native
Wayland client — confirmed via `xwininfo -root -tree` finding no trace
of it while a real window was visibly open (only Sommelier's own stub
windows appear). Wayland deliberately keeps window placement and focus
policy in the compositor, not the client, by protocol design.

Documented at `design.kb/040-design.kb/window-control.kb/` (new
sub-kb, anchored via two new entries — `020-goals.kb/undisruptive-launch.md`
and `030-requirements.kb/undisrupted-operator-input.md` — since no
existing goal/requirement covered operator-side launch UX, only
site-stealth and dev-safety). `probe-window-control.mjs` there is a
consolidated, re-runnable instrument for when the compositor changes.

**Alternatives considered:** None of the above are really alternatives
to each other — they're all "same idea, different lever," tried in
sequence as each one failed. The actual alternative, not yet built, is
gating window *creation* on an explicit operator action (keypress)
instead of trying to control an already-created window from the
client side; filed as `.claude/todo.kb/2026-08-15-000-*`.

### `Target.createTarget({background: true})` is not a general focus-theft fix — reconciling with `2026-08-14-000`

**Rationale:** That earlier entry backgrounded a *second* page (the
UA-metadata probe) inside a browser that already had a foregrounded
window holding focus — Chromium's own tab-activation logic, which does
respect `background`. Tonight's trial backgrounded the *first and only*
window of a freshly launched browser process (via `--no-startup-window`)
— a brand-new toplevel surface, whose initial keyboard focus is the
compositor's call, not Chromium's. Same CDP parameter, two different
mechanisms; only the first is proven to work. A future reader skimming
`2026-08-14-000` alone would reasonably conclude `background: true`
already solves focus-stealing — it doesn't, for the case that matters
here.

## Conventions Established

- When a Wayland/window-management question comes up in this
  environment, don't reason from X11-era assumptions (position
  flags, `xdotool`/`wmctrl`, un-minimize) — the compositor here is a
  hard boundary the client cannot cross, verify live before proposing
  a fix that assumes otherwise.
- `background: true` on `Target.createTarget`/`newPage` means "don't
  activate this tab within the browser" (works), not "don't let the OS
  focus this window" (doesn't, when it's the browser's first window).

## Open Questions

None — the investigation is conclusive (three independent levers, all
compositor-owned). The open item is implementation, not investigation:
tracked in `.claude/todo.kb/2026-08-15-000-Gate-capture-window-creation-on-explicit-operator-readiness.md`.

## References

- `design.kb/040-design.kb/window-control.kb/wayland-window-control-is-compositor-owned.md`
  — full measurement table
- `docs/dev/devlog/2026-08-14-000-Startup-flashes-eliminated--session-restore-forced-off--UA-probe-backgrounded.md`
  — the `background: true` success case this entry distinguishes from
- `.claude/todo.kb/2026-08-15-000-Gate-capture-window-creation-on-explicit-operator-readiness.md`
  — the still-open fix
