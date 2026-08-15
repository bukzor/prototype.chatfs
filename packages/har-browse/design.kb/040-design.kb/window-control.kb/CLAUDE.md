---
why:
  - undisrupted-operator-input
---

# Window Control

What we can and cannot make the launched browser window do, on this
native-Wayland (Crostini) development environment, before content is
ready.

Every OS-level window-state lever we tried — position, minimize,
initial focus — turned out to be compositor-owned, not
client-controllable. That's an empirical, environment-specific finding,
not a matter of picking the right flag; the measurements go stale as
the compositor changes.

## What belongs here

- Techniques tried, live/human-verified, and their outcome.
- Enough detail (date, method, exact flags/CDP calls) to re-run.
- Variants ruled out, so the next author does not re-propose them.

## What does NOT belong

- The mechanics of applying whatever we ship → `src/host_puppeteer.mjs`.
- The splash-overlay mitigation (a different problem: masking visual
  jank, not focus theft) → `070-future-work.kb/`.

## Re-measuring

`probe-window-control.mjs` is the instrument: each trial paints a
full-viewport page naming the expected state (or, for the focus trial,
an input box with a live readout of what it captured), holds, and asks
a human observer. Update the table in `wayland-window-control-is-compositor-owned.md`
in place with a new date rather than appending a second round — a
stale row that disagrees with a fresh one is worse than no row.
