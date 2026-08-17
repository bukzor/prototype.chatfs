---
managed-by: Skill(llm-subtask)
status: open
cost-benefit-sweh:
  timebox:
    "@value": 1.5
    rationale: |
      Extends an existing, already-generalized mechanism (chatfs.layout's
      view-tree construction, currently instantiated once for Created=)
      with one more instance, using data chatfs already computes per-uuid.
      No new capture/data-collection work. Should be small; timeboxed
      slightly above a trivial estimate because "generalize the mechanism
      cleanly" is a design judgment call, not pure mechanical repetition.
    confidence: tentative
  benefit-2w:
    "@value": 1
    rationale: |
      Any consumer that currently needs "which conversations are
      pulled/rendered vs. only captured" has to re-derive it by checking
      .chat/$UUID vs .data/$UUID directly. A generated view removes that
      from every such consumer, present and future, not just one.
    confidence: unsure
---

# Generalize the Created= symlink-view mechanism; add a pulled/unpulled status view

**Priority:** Low-medium — cheap, low-risk, no external deadline, but
unlocks external consumers who would otherwise re-derive this themselves.
**Complexity:** Low — extends an existing pattern; no new data collection.
**Context:** `chatfs.layout` (`packages/chatfs-cli/lib/chatfs/layout.py`)
already builds one such view: `$root/YYYY/MM/DD/HH:MM:SS±HH:MM/$TITLE/`,
a directory-symlink per chat pointing at `.chat/$UUID/`, generated from
data chatfs already holds (`created_at`). Its own docstring frames this
as general path arithmetic, not a one-off. See also
`packages/chatfs-cli/design.kb/040-design.kb/chat-as-directory.md`.

## Problem Statement

chatfs's storage already separates "captured" (`$root/.data/$UUID/`
exists) from "rendered/promoted" (`$root/.chat/$UUID/` exists) — this is
inherent in the two-tree layout, not new information. Nothing currently
exposes that distinction as a queryable view the way the `Created=` date
attribute already is. A consumer that wants "list everything pulled" or
"list everything captured-but-not-yet-rendered" has to know the two-tree
internals and check presence/absence itself.

## Requirements

Stated at increasing levels of detail — later bullets are more specific
elaborations of earlier ones, not additional independent requirements.

1. chatfs should expose derived corpus-attribute views as generated
   symlink forests — the same shape as the existing `Created=` view —
   for attributes it already has the data to compute, rather than
   requiring each external consumer to re-derive that view itself.
2. The first such new view: pulled vs. unpulled/captured-only status.
   This needs no new data collection — it's exactly the existing
   `.chat/$UUID` vs. `.data/$UUID`-only distinction, already known
   per-uuid today.
3. The mechanism belongs alongside the existing `Created=` logic in
   `chatfs.layout` (i.e., grows the same module/capability), not
   reimplemented by a downstream consumer.
4. Explicit non-goal for this task: do not extract the "attribute →
   symlink forest" mechanism into a separate, cross-repo/shared library.
   That's warranted once a second, non-chatfs consumer of the same
   trick exists — not before.

## Current Situation

- `Created=YYYY/MM/DD/...` exists today, per provider
  (`~/chats/{claude,chatgpt,aistudio}/Created=...`), confirmed generated
  and symlink-based.
- `.data/$UUID/` (captured) and `.chat/$UUID/` (rendered/promoted) are
  already separate, well-defined trees per `chatfs.layout`'s own
  docstring — the pulled/unpulled distinction is a direct read of their
  presence, not a new concept.
- No pulled/unpulled view exists yet.

## Proposed Solution

Left open, deliberately — see Open Questions. The Requirements section
above is the actual spec; implementation shape (naming, exact directory
convention, whether generation is triggered at render time vs. on
demand, per-provider vs. root-level) is not decided and shouldn't be
inferred from this task beyond what's stated above.

## Open Questions

- Naming/directory convention for the new view (parallel to `Created=`,
  or a different scheme) — unresolved, intentionally not specified here.
- Regeneration trigger: recomputed as part of the existing
  capture/render pipeline, or a separate on-demand step? The `Created=`
  view's own trigger is confirmed: `chatfs.shell.place` calls
  `time_dir_for` at render time (`chatfs/shell/place.py:167`) — i.e.
  it's built as part of promoting `.data/$UUID/` to `.chat/$UUID/`, not
  a separate batch job. Matching that trigger is the natural default,
  but whether pulled/unpulled status should follow the same trigger
  wasn't confirmed as part of this task's scope.
- Does "status" want more than two states eventually (e.g., captured
  but capture incomplete/errored)? Out of scope now — two states
  (pulled / captured-only) is the agreed starting point.

## Success Criteria

Also at increasing levels of detail:

- [ ] **Minimum:** for at least one provider, a generated view exists
      that answers "list every pulled conversation" and "list every
      captured-but-unpulled conversation" without custom code beyond
      `ls`/`find`.
- [ ] **Correctness:** the view is generated, not hand-maintained, and
      matches actual `.chat/`/`.data/` presence at generation time — no
      view content that can silently drift from disk truth.
- [ ] **Uniformity:** the view exists per-provider, matching how
      `Created=` already exists under each of `claude/`, `chatgpt/`,
      `aistudio/` — not built for just one provider and left as a gap
      for the others.
- [ ] **Generality (stretch):** the underlying mechanism is structured
      so that a future third or fourth attribute could be added without
      restructuring this one — i.e., nothing here hardcodes "status" in
      a way a sibling attribute couldn't reuse. Not required to actually
      add another attribute now, just not to foreclose it.

## Notes

### Addendum: motivating use case (context only, not scope)

This task surfaced while designing a corpus-navigation/indexing approach
for a different repo's own conversation-history corpus
(`~/claude/meta-reasoning`, its `2026-08-14--source-survey/` and
`corpus-index/`). That project needed exactly a pulled/unpulled
distinction and, investigating how to get it, found chatfs already had
the underlying data and an existing generalizable mechanism to hang it
on — hence this task living here instead of being rebuilt there.

This provenance shouldn't narrow the scope above: the requirements are
written to stand on their own as a chatfs capability, useful to any
consumer, not tailored to that one project's needs.
