# 2026-07-06: chatfs-mockup-chatgpt — chatgpt fork-fact parity via shared chatfs_render.py

## Focus

Close the last open item of the provider-code-reuse stutter-step: chatgpt
fork-fact notation parity, with `chatfs_claude_conversation_render.py` as
the reference. Overnight autonomous session; user review pending.

## What Happened

**Review of the reference found three defects; user directed fixes** (commit
`ad9ac4c`, TDD, golden test):

1. **Pruned current leaf silently emptied the live set.** If the recorded
   `current_leaf_message_uuid` is a bodiless cancel that pruning dropped,
   `live_ancestors` returned `{}` and every fork silently fell to
   latest-wins — `←latest` appearing on what is really the trunk. Now
   asserted (`current` must be a tree node). No demo trips it; the assert
   is there to catch the day one does.
2. **created_at ties broke toward the first sibling.** `max()` keeps the
   first maximal element; claude timestamps are second-resolution, so
   same-second regenerations can tie. Ties now fall to the last-listed
   sibling — the best guess at "latest" all else equal.
3. **Depth-keyed dividers fragmented branches into look-alike islands.**
   The old conditional keyed on depth deltas, so "aside opens one level
   deeper" and "branch resumes after its nested aside" both rendered as a
   bare blank line — two meaningfully different transitions, visually
   identical, and a single dead branch shattered into multiple blockquote
   islands. The walk order means only four transition kinds exist
   (continuation, sibling attempt, aside-open, branch-resume); the new
   conditional keys on branch-head-ness: sibling attempts get the `---`
   rule at the fork's depth, everything else gets a blank quoted at
   `min(depth, prev_depth)`. Net effect: **the markdown blockquote
   structure now mirrors the tree** — each branch is one contiguous island
   containing its nested asides. Only demo `960e14cf` (the one with ≥2-deep
   forks) changed: 14 divider sites, all blank→quoted-blank.

**Parity landed by extraction, not duplication** (commit `4995320`).
`chatfs_render.py` now owns the fork-fact contract end to end: `Turn`,
`ConversationTree` (ids, parent/children structure, epoch creation times,
live leaf), live/primary selection, numbering, `Renderer`, `render_tree`.
Provider renderers reduce to their own wire shapes:

- claude: 3-part stems, all-zero root sentinel, `prune_bodiless_leaves`.
  Output byte-identical across all four demo conversations.
- chatgpt: 4-part stems, `mapping`/`current_node` (with a new
  parent↔children cross-check), and `normalize_turnless`.

**Key decision — normalize into the invariant, don't parameterize the
renderer.** The renderer's strength is its strong invariant (every non-root
node has a turn); chatgpt's tree legitimately violates it (system
placeholders, empty thought summaries, bodiless non-leaves). Rather than
threading provider callbacks through the shared core, `normalize_turnless`
repairs the tree up front: turn-less leaves drop, turn-less pass-throughs
splice out (child takes the parent's sibling slot, preserving reply order),
and a turn-less **fork** gets a synthetic heading linking its `.json`
record — so fork facts always have a numbered anchor. Claude's origin
materialization is the root-sentinel instance of the same idea. Data IR
over callbacks: inspectable, diffable, testable pure.

**chatgpt heading changes** (deliberate, parity-driven): date-to-the-minute
times replace bare `HH:MM:SS` (cross-provider consistency; full timestamp
still in the link); the content-type qualifier survives via the new
`Turn.note` field; numbers gain branch prefixes (`105/124`).

**Verification:** both chatgpt demos render with body text and turn order
byte-identical to the old renderer (quote/heading/subtitle-stripped
projection diff is empty); turn counts unchanged (206/129 — no synthetic
anchors needed on this data, no turns lost); fork facts present at all 5+12
fork nodes. `normalize_turnless` unit tests were mutation-checked (positional
splice → append, fixpoint → single pass) since they were written post-hoc.
15 tests, basedpyright clean across the incubator.

## Decisions / Conventions

- **The fork-fact notation has one home:** `chatfs_render.py`'s module
  docstring carries the contract (acceptance criteria, excerpt-reader
  redundancy, numbering stability); provider docstrings point at it.
- **Tie-break convention:** creation-time ties fall to the last-listed
  sibling, everywhere (shared `primary_child`).
- **chatgpt's old tie behavior** (ties→first, and bodiless fork children
  ranked at epoch 0.0) is gone: primary selection now runs post-splice on
  real creation times.

## State

- Committed `ad9ac4c` (renderer fixes + golden test) and `4995320` (shared
  extraction + chatgpt parity) on `main`; **not pushed** — overnight
  session, user reviews first.
- Render comparisons preserved in `trash/fork-parity/{before,after,shared}/`.

## Loose Ends

- aistudio has no conversation renderer yet; when it grows one it should be
  a third thin consumer of `chatfs_render.render_tree`.
- The extraction-side unification items (shared `capture()`, persist every
  pluck output, endpoint cross-check, provider-complete `<details>`
  wrapping, pipe-vs-delegation) from
  `.claude/todo.kb/2026-07-03-000-…pre-unification-fixes…` are untouched —
  this session was render-side only.
- `chatfs_render.py` is incubator-local, matching the `chatfs_layout.py`
  home decision; promotion to `packages/chatfs-core/` remains future work.
