# Devlog: 2026-07-09 — chatfs-mockup-chatgpt todo backlog sweep

## Focus

Work through the open backlog in `.claude/todo.md` after the 2026-07-06
fork-fact parity landing and the 2026-07-08 code-half review closure.
Closed four items; several remain, three of them genuinely blocked on
the user rather than just unstarted (see Open Questions).

## Decisions

### The match/case sweep found no genuine enum dispatch — explicit `if`/`elif`/`else` instead

The todo item ("scan for the implicit-match / `if X: return` …
fall-through pattern, convert to explicit `match`/`case`") assumed the
fix would look like `chatfs_claude_conversation_splat.py`'s existing
`match`/`case` blocks (a real closed-variant dispatch: text/thinking/
tool_use/tool_result). Auditing `chatfs_chatgpt_*.py` and both
`*_render.py`, the only three violations found —
`chatfs_render.py::primary_child`, `chatfs_render.py::divider`,
`chatfs_chatgpt_layout.py::_created` — are all "return early, fall
through to a bare trailing statement" on a two-way condition, not a
finite set that could gain members. Per the house style rule
(`~/.claude/reference.kb/python/style.md` "Explicit else, never
implicit"), a two-way bool else just returns the other value — so each
became explicit `if`/`elif`/`else`, not `match`/`case`.

**Alternatives considered:** Forcing `match`/`case` onto `primary_child`
anyway, for uniformity with the splat file. Rejected: `match`/`case` on
a non-variant condition doesn't buy exhaustiveness (the style rule's
actual goal) and reads as pattern-matching where there's no pattern to
match, just a boolean.

### chatgpt's `main()` needed a pure-pipeline extraction before it was testable

The chatgpt normalize_turnless test gap (a turn-less fork's synthetic
anchor, and `primary_child`'s tie-break, both unverified against
chatgpt's actual wire shape) couldn't be closed by writing tests against
existing code: `make_turn` was a closure inside `main()`, and there was
no `render_conversation`-equivalent pure function like claude's
renderer already has (only `main()`, doing I/O and computation inline).
Extracted `make_turn(nid, stems)` and
`render_conversation(conversation, stems, turns)` as top-level functions
first — confirmed behavior-preserving (byte-identical output on both
demo captures with a real `conversation.json`, before/after) — then
wrote `chatfs_chatgpt_conversation_render_test.py` against the new
pure functions.

**Verification:** hand-applied two mutations (flip the tie-break
direction; swap the synthetic anchor's `.json` link for `.md`) and
confirmed each turned exactly the new tests red, then reverted. Lighter
than the full `Skill(mutation-testing)` procedure (which is for
systematic coverage sweeps, tracked in `mutation-testing.kb/`) — this
was a single known, already-identified gap, not an audit.

### `provider-plugin-model.md`: promoted from symlink to a real entry, grounded in landed code

The incubator's copy was a symlink to the parent project's abstract
spec. Promoted to a real entry recording the concrete three-way split
observed building three providers (chatgpt, claude, AI Studio) side by
side: byte-for-byte-identical helpers (→ `chatfs_layout.py`/
`chatfs_render.py`), the 3-value `id`/`title`/`created` adapter every
provider's `place_meta` wrapper shares, and what's genuinely
provider-only (AI Studio's JSPB `index_item` synthesis, claude's
misfiled `capture()`). Verified against the actual `place_meta` wrapper
in all three `chatfs_*_layout.py` files before writing, not from memory.

**Correction caught by the user:** the todo.md item's own wording said
"two-provider lessons" — stale from before AI Studio landed as the
third provider (2026-06-20), carried forward uncritically into my
"done" note. Fixed there, and swept the sibling
`todo.kb/2026-05-11-001-shared-code-among-providers.md`, which had the
same staleness (a "signal weak at two providers" Priority line, and an
unresolved-but-actually-answered rule-of-three Open Question) even
though its own body already recorded the extraction landing 2026-07-05.

### Dangling references to a deleted sessions.kb note

Session-start deleted two `~/.claude/sessions.kb/` entries
(`provider-code-reuse-stutter-step.md`,
`pyright-clean-sweep-across-the-incubator.md`) as fully closed per git
history (`7ba1669`, `a82d1f7`) — their follow-ups were already absorbed
into `todo.md`. That left two dangling in-repo references to the first
file (`todo.md`'s cross-provider-drift item, and
`chatfs_claude_layout.py`'s module docstring). Redirected both to where
the content actually lives now: `provider-plugin-model.md` for the seam
analysis, the cross-provider-drift todo.kb file's own "Solve by
unification" section for `capture()` tracking.

## Conventions Established

- A "convert to match/case" todo item should be read as "make the
  exhaustiveness explicit" (the style rule's actual concern), not
  literally "use `match`/`case` syntax" — a two-way condition wants
  `if`/`elif`/`else`, not a forced pattern match.
- Deleting a stale sessions.kb entry means grepping the *project* for
  references to it, not just deleting the file — house `sessions.kb/`
  entries can be linked from inside project docstrings/todos.

## Open Questions

- Blocked on the user, not on effort: AI Studio's index rung and the
  har-browse `has_more=false` wait fix both need a live authenticated
  browser session; claude-code-as-next-provider has its own open design
  questions (locator shape, `claudecode`/`claudeai` naming collision,
  sequencing) that CLAUDE.md says to discuss before writing; the
  cross-provider-drift file's driver-model question (pipe vs.
  delegation) says "decide once, document" — a real decision point.
- Not blocked, just not reached this session: branch enumeration in
  splat, the debug-intermediates flag, the incubator rename, and the
  shared-code boundary-refinement question (what else belongs in
  `chatfs_layout.py`, incubator-local vs. `packages/chatfs-core/`).

## References

- `.claude/todo.md` — updated inline with done-notes for each closed item
- `~/.claude/sessions.kb/penguin/chatfs-mockup-chatgpt-open-todo-sweep.md`
  — session tracking note with the same status, for cross-session pickup
- Commits: `a5c8bce`, `29274b9`, `c968a22`, `f85d485`, `9921678`
