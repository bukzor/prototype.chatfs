---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 2.0
    rationale: >
      Descriptive v1 only: write down who owns/writes/reads which
      subpaths in the current pipeline. The considered revision (next
      maturity stage) is a separate, unestimated track.
    confidence: tentative
  benefit-2w:
    "@value": 1.0
    rationale: >
      Unblocks daemon design (child 004) and the stack-split rewrite
      (child 005); also the reviewable artifact the user wants to tweak
      per se.
    confidence: tentative
---

# Path-ownership contract, v1 (descriptive)

**Priority:** High — independent; unblocks two other children.
**Complexity:** Low
**Context:** Decided 2026-07-13: the Rust↔Python seam is documented as
*path ownership* — which subpaths each component wholly owns
(read/write) vs merely reads — not as command/argument enumeration
(commands and args stay single-sourced in the owning package; reference,
don't duplicate). Home: `docs/dev/technical-policy.kb/` (normative,
cross-cutting, reviewable per se).

## Problem Statement

`black-box-decomposition.md` says the daemon depends only on "command
invocation, exit codes, file paths, atomic outputs" — but no document
states which paths belong to whom. Integration design needs that seam
written down; today's `$PWD` reality is the v1 content.

## Implementation Steps

- [x] Write `docs/dev/technical-policy.kb/path-ownership.md` covering the
      current chat-dir anatomy: `.chat/$UUID/.data/` (capture stages
      write; everything else read-only), derived members `messages/`,
      `conversations/`, `chat.md` (render owns, regenerates
      destructively — atomicity per the atomic-regeneration todo), view
      symlinks in the date tree (index splat owns), and the cache root
      as an argument everywhere (no baked default). Landed 2026-07-14:
      cache root turned out to be a baked default today (not an
      argument anywhere), so that bullet is `[!TODO]`-marked rather
      than descriptive — see the doc's Cache root section.
- [x] State the future daemon's position descriptively where true today,
      `> [!TODO]`-marked where not (e.g. "the mount daemon owns `control`/
      `status`/`needs_sync` paths; it writes nothing under `.chat/`").
- [x] Cross-link: `black-box-decomposition.md`, `work-enqueueing-model.md`,
      the atomic-regeneration todo; child 005 will point `stack-split.md`'s
      rewrite here. Also linked `sync-control-plane.md` (source of the
      control-plane path names) and the incubator's `chat-as-directory.md`
      (storage-vs-view rationale).

## Open Questions

- None for v1 — it is deliberately descriptive. Anticipated tweaks are
  the considered track, reviewed as design discussion when the user
  wants it.

## Success Criteria

- [x] A reader can answer "may component X write path P?" for every
      component and subpath in the current system without reading code.
- [x] No command names or argument lists duplicated into the doc.
