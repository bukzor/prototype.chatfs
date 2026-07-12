# noun=conversation, verb=render

Render emits markdown for a conversation. The bare leaf
(`chatgpt conversation render <chat-dir>`) walks `mapping` from root
toward `current_node` in `.data/conversation.json`:

- Live-path turns render unprefixed.
- Dead-branch turns appear immediately after their fork point,
  blockquote-prefixed at fork depth — they read as quoted asides between
  the parent turn and the live continuation. A branch and its own nested
  asides form one contiguous blockquote island (boundaries inside a
  branch are blank lines quoted at the shallower depth); a `---` rule at
  the fork's depth separates adjacent sibling attempts.
- Each turn is `# [number · role · time](messages/<stem>.md)` — H1
  backref to the atomic turn-file under `messages/`. `number` is the
  branch-prefixed numbering below; `time` is wall-clock date to the
  minute (the link's stem keeps the full timestamp). The link form is
  the discriminator: only turn headings are heading-as-link, so
  `^(> )*# \[` finds turns and never a body's own `#` headings.

The bare leaf reads `.data/conversation.json` and `messages/*.json` to
find each turn's stem; it does not manage placement and writes markdown
to stdout.

## Fork-fact notation

When the tree forks, the render makes the fork legible from headings and
metadata alone. The governing audience is the *excerpt reader* (grep
window, partial read): no single fact may live in only one place if a
reader landing elsewhere would need it, so fork facts repeat across
positions.

- **Numbering** is branch-prefixed: a branch member is `head/seq`
  (`049/051`); trunk and branch-head turns render bare (`049`). Numbers
  are stable cross-reference handles, not chronology -- stable within a
  render, but regenerating a grown conversation renumbers (seq is emit
  order); the durable handles are the link stems.

  > [!TODO]
  > Sought: numbering that never drifts across regenerations -- no
  > hysteresis, no oracles (technical-policy: `stable-references.md`,
  > `determinism.md`). Chronological rank is append-stable by
  > construction (new turns always timestamp last) and collapses toward
  > the stem ordering -- one reference system -- but numbers stop
  > matching reading order and the `head/seq` prefix scheme needs
  > rethinking. A path-shaped scheme (one segment per fork depth) is
  > the other candidate. Either obsoletes the caveat above.

- **`(re: N)` backlink** on the heading whenever the parent is numbered
  but isn't the turn rendered directly above -- the fork's live
  continuation (asides pushed its parent away) and each later sibling
  attempt both carry it.
- **Metadata lines** sit in two zones around the body, by *direction*:
  - *Above* the body — version **status**, read before deciding to engage:
    `superseded by: <winner>` on each abandoned sibling (one hop to the
    live continuation from any excerpt); `prior revisions: …` on the
    winner (succession order — the revision chain recoverable in one
    canonical place, landing right after the superseded asides it names).
  - *Below* the body — forward **navigation**: `replies: …` on a fork
    parent, all children in render order with the chosen continuation
    marked `←live` when it's on the path to the conversation's current
    leaf, or `←latest` when it's merely the most-recently-created child of
    a branch that's already superseded — the two are different claims and
    must not share a label.
- **Spelling is bare `*italics*`, not `<sub>`.** The primary consumers are
  LLMs and plaintext editors, to which `<sub>` tags are token cost and
  visual clutter; in-browser smallness would serve only the third-ranked
  consumer. Same reasoning that keeps **anchors** out: refs repeat the
  heading's number verbatim, so a search for a ref string finds the
  definition — the heading *is* the anchor, no `<a id>` needed.
- **`←live` is explicit, not positional.** Liveness must not rely on the
  unstated "last in the list is live" convention.
- **Dividers key on branch identity, not depth deltas.** A later sibling
  attempt gets a `---` rule at the fork's depth; every other boundary
  is a blank quoted at the shallower of the two adjacent depths, so the
  blockquote structure mirrors the tree — each branch is one contiguous
  island containing its nested asides.

  > [!TODO]
  > The rule is `***` (the same thematic break): message bodies --
  > chatgpt's especially -- are full of `---` hrs at every quote depth,
  > including bare at depth 0, so a `---` splitter is only heuristically
  > findable; the demo corpus contains zero `***` lines. Lands with a
  > `divider()` change plus regenerated goldens and demos.

> [!TODO]
> Markers are convention-rare, not unambiguous by construction:
> `^(> )*# \[` and the island rule are reliable on today's corpus, but
> body text could counterfeit either. Whole-file consumers have
> `.data/conversation.json`; the excerpt reader has only the window, so
> the line shapes themselves must discriminate. Sought: shapes body
> prose cannot produce.

> [!TODO]
> Deconflict excerpt redundancy with local noise: fork facts repeat
> across positions for the excerpt reader (governing), at the cost of
> near-duplicate facts landing within one window (e.g. `(re: N)` two
> lines below a divider that implies it). Excerpt sufficiency dominates;
> a design serving both is wanted. **Why not a `re:` divider subtitle**
> (moving the backlink off later attempts' headings): breaks heading
> uniformity and starves the heading-centered grep window -- rejected.

This notation is **provider-agnostic** — it's a property of rendering a
forked conversation, not of any one provider's capture. It is written
once, in `chatfs_render.py` (`Turn`/`ConversationTree` in,
markdown out); each provider renderer reduces its wire shape to that
seam, repairing its legitimately turn-less nodes first — chatgpt via
`normalize_turnless` (drop turn-less leaves, splice pass-throughs,
materialize a synthetic heading at a turn-less fork so fork facts always
have a numbered anchor), claude via the narrower `prune_bodiless_leaves`.

The orchestrator forms prepare inputs and place outputs. `path render`
purges non-captured content (allowlist `{.data}`), splats
`.data/conversation.json` via `chatgpt-splat` (see `../../verb=splat.md`)
into `messages/` and `conversations/`, calls the bare leaf, and writes
the result to `chat.md`. `url render` thinly resolves the URL → chat dir
and delegates to `path render`.

Deterministic regen: orchestrator forms rebuild the splat tree and
`chat.md` from `.data/conversation.json` on every invocation. See
`../../deterministic-regeneration.md`.

## AI Studio divergence

AI Studio's wire shape has no fork representation at all — no
parent/child field anywhere, a flat `chunkedPrompt.chunks` list in
document order (see `dev.kb/claims.kb/aistudio-jspb-prompt-shape.md`,
"Turn order is linear"). `chatfs_aistudio_conversation_render.py`
builds a straight predecessor chain (each turn's parent is the one
before it) and hands it to the *same* `chatfs_render.render_tree` —
no bespoke linear renderer. The fork-fact notation above degenerates
to a no-op on every node (no `replies:`/`superseded by:`/`(re: N)`
ever appears), by construction, not by a provider-specific special
case. `path render`'s splat produces only `messages/`, never
`conversations/` — there is no branch to enumerate.
