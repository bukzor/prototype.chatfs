---
status: observed
first-recorded: 2026-05-12
last-checked: 2026-05-12
evidence:
  - claude.chat.b0f46746-e087-44de-9d34-ce0e15027d6b.jsonl  # exhibit: chat capture missing /chat_conversations_v2
previously-claimed:
  - text: "/recents doesn't fire chat_conversations_v2 until the user scrolls"
    where: docs/dev/design-incubators/chatfs-cli-mockup/.claude/todo.md (parity ladder, Browse-side automation; corrected 2026-05-12)
    when: 2026-05-11
---

# har-browse CDP can trail visual interactability

When har-browse is told to stop ("Done Capturing") shortly after the
browser sidebar becomes visually interactable, the emitted CDP stream
may be missing later index pages that *would* have appeared if the
session had been allowed to run longer. The interactable-UI ≠
captured-stream-complete; there's a delay window.

## Cause

**Underdetermined.** Possibilities — none confirmed:

- Sidebar paginates on scroll
- Sidebar fetches lazily on a delay/idle timer
- Sidebar paginates on focus or visibility events
- har-browse's "capture done" cutoff races with in-flight requests

## Mitigation

A downstream stop-when filter that breaks on `has_more=false`
triggers EPIPE-clean shutdown of har-browse (per
`packages/har-browse/.claude/todo.md` item 2026-04-24-003, which has
landed). No timing heuristic needed: the pluck side knows the
termination predicate and signals upward.

## How this settles

Not directly settleable without instrumentation that distinguishes
the candidate causes. Practical resolution: implement the stop-when
filter on the claude index pipeline; that sidesteps the question for
production use. If we ever want to know the cause, we'd:

1. Reproduce with the browser kept open for N minutes after
   interactability
2. Diff resulting CDP against the "Done Capturing immediately"
   version
3. Correlate timing of `chat_conversations_v2` events against
   browser-side events (scroll, focus, idle)

## Why this matters

I propagated the "doesn't fire until scroll" claim into a session
response without rederiving it from evidence — a single-source-of-
truth lookup that should have been a fact-check. The user flagged it
and corrected the underlying todo. Recording the bad version
verbatim under `previously-claimed:` so future agents can pattern-
match if they see "doesn't fire until scroll" language anywhere else
in the repo (stale comment, devlog, etc.) and treat it as suspect.

## See also

- `claude-sidebar-fires-chat-conversations-v2-on-chat-page.md` —
  a related live-behavior claim, handled as `status: assumed` with
  fail-loud guardrail in `url_browse.py` rather than asserted.
- `learnings.kb/assume-and-assert-pattern.md` — discipline that
  replaces single-source inference with empirical-test-as-code.
