---
managed-by: Skill(llm-subtask)
status: active
---

# Gate capture-window creation on explicit operator readiness

**Priority:** medium — real UX bug (operator's keystrokes get eaten), but
workaroundable today (pause before invoking `har-browse`).
**Complexity:** small-to-medium once the design is picked; the hard part
(figuring out what's even possible here) is done.
**Context:** `design.kb/030-requirements.kb/undisrupted-operator-input.md`,
`design.kb/040-design.kb/window-control.kb/`.

## Problem Statement

Invoking `har-browse` launches a headful Chromium window that
immediately steals OS keyboard focus, before content is ready. Any
keystrokes the operator is mid-typing elsewhere (this chat, a
terminal, an editor) land in the new window instead — live-verified
2026-08-14, `design.kb/040-design.kb/window-control.kb/wayland-window-control-is-compositor-owned.md`.

## Current Situation

Every client-side lever tried to *prevent* the OS from stealing focus
failed under this native-Wayland (Crostini) environment, including
CDP's purpose-built `Target.createTarget({background: true})`. That's
compositor-owned policy here, not something `src/host_puppeteer.mjs`
can override — see the doc above for the full table.

`page.bringToFront()` (`src/host_puppeteer.mjs` ~line 386) is
unrelated to the steal: the baseline trial (no `bringToFront()` call
at all) stole focus too. Removing it would not fix this.

## Proposed Solution

Don't fight the compositor — avoid needing its cooperation. Delay
window creation until the operator gives an explicit, deliberate
readiness signal (e.g. the CLI prints a prompt and blocks on a
keypress/Enter before calling `puppeteer.launch()`). Focus transfer
then only ever follows something the operator just did on purpose, so
there's never an unexpected steal mid-keystroke.

## Implementation Steps

- [ ] POC the keypress-gate in `trash/`, live-verified per standing
      session policy (nothing unproven goes in `src/`): type
      continuously elsewhere spanning the gate and the window's
      creation; confirm zero characters land in the capture window.
- [ ] Decide UX: what the prompt says, whether `--howto` mode needs a
      different gate (it already expects the human to be reading
      instructions right before the window appears — reconcile so the
      gate doesn't fight that flow).
- [ ] Land the gate in `src/har_browse.mjs` / `src/host_puppeteer.mjs`.
- [ ] Add a `tests/` regression per the usual coverage bar (may need a
      fake/skippable gate for headless CI runs — `--headless` runs
      shouldn't block on a keypress that can't come).
- [ ] Update `design.kb/030-requirements.kb/undisrupted-operator-input.md`
      verification note once shipped; unwrap any `[!TODO]` this work
      introduces there.

## Open Questions

- Does `--headless`/windowless mode need the gate at all? It has no
  window and no Done button already (unattended-only), so likely no —
  confirm and make the gate a no-op there rather than a hang.
- Is a bare keypress enough, or does the operator want to see *what*
  they're about to launch (URL, profile) before committing? Scope
  creep risk — default to the smallest thing that passes the success
  criteria below.

## Success Criteria

- [ ] Live/human-verified: typing continuously into another
      application spanning a `har-browse` invocation produces zero
      captured characters in the capture window, in the default
      (no extra flags) invocation.
- [ ] `--headless` / windowless runs are unaffected (no new blocking
      wait).

## Notes

Session narrative: this session's live-verification chain (position →
minimize → focus, each proven to fail) is in
`design.kb/040-design.kb/window-control.kb/wayland-window-control-is-compositor-owned.md`,
re-runnable via the sibling `probe-window-control.mjs`. Don't
re-derive it — start from that doc.

A secondary, separate finding from the same session: an injected
full-viewport DOM splash overlay (`evaluateOnNewDocument`, same
mechanism as the Done-button overlay) cleanly masks real page content
until removed, proven live twice (`trash/probe-overlay-splash.mjs`,
`trash/probe-overlay-splash-once.mjs`). That fixes visual loading
jank, not this bug (a DOM overlay doesn't change OS keyboard
routing) — unrelated unless a future session wants that nicety too.
