# 2026-05-05: chatfs-mockup-chatgpt — design.kb consolidation

## Focus

Audit the incubator's `design.kb/` for inconsistencies between the
older (Apr 29–30) entries and the newer (May 5) `chat-as-directory.*`
wave; resolve contradictions; promote durable historical rationale
to an ADR.

## What Happened

**Found two waves.** The Apr 29–30 entries
(`browse-incidental-capture`, `cli-command-shape`, `no-partial-synthesis`,
`stdio-pipeline-shape`) and the README all describe the **flat
ts-dir layout** (`meta.json`, `cdp.jsonl`, `$UUID.json`, `$UUID.splat/`,
`$TITLE.md` siblings). The May 5 entries
(`chat-as-directory.md` + `chat-as-directory.kb/*`, plus the rewritten
`deterministic-regeneration.md`) describe the **`.chat/$UUID/`
storage + symlink view** layout. Code still implements the Apr layout;
the May docs are aspirational. Most propagation work tracked in
`.claude/todo.kb/2026-05-05-000-…-propagate-to-other-docs.md`.

**Resolved five extra inconsistencies the propagation todo did not
already cover:**

- `title.txt` lifecycle was contradictory (parent listed it as captured;
  sub-kb's `captured-vs-derived.md` listed it as derived; `place_meta`
  in `pipeline-implications.md` wrote it from capture-side). User
  judgment: redundant with view-symlink filename + `meta.json.title` +
  potential `chat.md` frontmatter — drop entirely from canonical
  storage. Removed from four files.
- Same-layer `why:` references: `chat-as-directory.md` points at
  sibling `canonical-conversation-graph` in 040. Skill text said
  "upward only." User policy: same-layer is allowed. Updated
  `Skill(llm-design-kb)` source.
- `chat-as-directory.kb/*.md` lacks `why:` frontmatter — user OK,
  inheritance-from-parent is implicit.
- `index_splat` violated the "addressable target" rule from
  `stdio-pipeline-shape.md`. The rule was overgeneralized; softened
  to allow fixed-by-convention root for stages with exactly one
  target. `index_splat` documented as the convention case.
- `path` locator now ambiguous (ts-dir vs `.chat/$UUID/`). One-line
  clarification in `cli-command-shape.md`: accepts either, normalizes
  internally.

**ADR extraction.** The "Why not freshness caches" section in
`deterministic-regeneration.md` was historical justification (1000h
CDP cache, 60min index cache, mtime-gated splat — all removed). Moved
to `docs/dev/adr/2026-04-29-000-no-freshness-caches.md` (new ADR
directory; matches the `Skill(llm-collab)` pattern). Trimmed the kb
entry to a forward-facing paragraph that points at the ADR.

**Provider stub via symlink.** Parent project already has
`docs/dev/design.kb/040-design.kb/provider-plugin-model.md`. Created
a symlink in the incubator's 040 layer pointing at it. If
chatgpt-specific detail accrues, replace the symlink with a real file
or sub-kb without changing the entry's name.

## Lessons

**The directory IS the listing.** First impulse was to add a per-entry
table to `040-design.kb/CLAUDE.md`. User overruled — the directory
itself is the list; CLAUDE.md should describe what belongs / does
not belong, never enumerate. "See also" pointers should reference
directories, not lists.

**Slim-in-place vs ADR extraction depends on the project.** Initial
plan was to slim `deterministic-regeneration.md` in place. After user
pointed at `Skill(llm-collab)`'s ADR convention, extraction was the
right move — the historical-justification content has its own home.
Slim-in-place is correct only when the project has no ADR practice.

## Next Session

- Item 000 in `.claude/todo.kb/`: propagate the chat-as-directory
  layout to the older Apr 29–30 docs (browse-incidental-capture,
  no-partial-synthesis, stdio-pipeline-shape examples), the README
  pipeline diagram (best done after implementation lands), and the
  cli-command-shape script-name table.
- Item 002 in `.claude/todo.kb/`: plan the noun-verb sub-kb
  (per-cell scope recommended). User has agreed it's worth doing
  before more verbs/nouns are added.
- Item 001: scan design.kb for promotion signals, lower priority.
- Implementation of `.chat/$UUID/` storage in actual code (
  `place_meta`, `path_render`, etc.) — design persisted, code
  pending.
