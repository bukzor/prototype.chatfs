# Devlog: 2026-07-12 — todo.md/todo.kb clear pass, dead-link cleanup

## Focus

Ran `Skill(llm-subtask)`'s `todo clear` over this incubator's backlog: verify
every `[x]` item in `.claude/todo.md` against a devlog record, strip the
verified ones out of the tactical list, and delete `todo.kb/` files whose
work is fully closed.

## Decisions

### Verify-before-delete surfaced one orphaned open item

`todo.kb/2026-07-03-000-cross-provider-data-flow-drift...md` was marked
`[x]` in `todo.md` and its own "Success Criteria" were all `[x]` — but one
nested `- [ ]` inside "Fix before unification" item 1 was never actually
closed: threading AI Studio's per-turn `createTime` into splat basenames
(noted as "deferred, not part of the crash fix" when the item was written
2026-07-03). It wasn't tracked anywhere else — not in `todo.md`, not in the
AI Studio parity-ladder file. Deleting the drift file as planned would have
silently lost it.

**Resolution (user's call):** promoted it to a standalone
`todo.kb/2026-07-12-000-AI-Studio--thread-per-turn-createTime-into-splat-basenames.md`,
referenced from `todo.md`'s `## Later` section, *then* deleted the drift
file. This is the same underlying gap already noted (or rather, half-noted)
in `devlog/2026-07-11-001-...`'s "Open questions" — AI Studio computes
heading timestamps at render time instead of baking them into basenames at
splat time like claude/chatgpt — so the new entry cross-links both.

**Alternative considered:** inline `todo.md` bullet instead of a new
`todo.kb/` file. Rejected (user's choice) — a real `todo.kb/` entry keeps
the reasoning/scope with the task instead of compressing it into one line.

### One item cleared without a devlog record

`chatfs_layout.py::time_dir_for`/`place_meta` test coverage (done
2026-07-12, commit `04d24a0`) had no matching devlog entry in either
`devlog/` directory. Per `todo clear`'s "if no match, ask user before
removing," asked; user's call: clear it anyway, treating the commit itself
as sufficient record. Not every completed item needs a devlog entry —
`todo clear`'s devlog-check is a *default* verification step, not an
absolute gate.

## Conventions Established

- `todo clear` isn't just "check devlog, then delete" — a file marked done
  at the top level can still have unresolved nested sub-items. Skimming a
  `todo.kb/` file's own checkboxes (not just trusting `todo.md`'s summary
  `[x]`) is a necessary step before deleting it.
- When a `todo.kb/` file is deleted, grep the whole repo (not just
  `todo.md`) for other files linking to it. Two living docs
  (`design.kb/040-design.kb/provider-plugin-model.md`,
  `todo.kb/2026-06-20-000-aistudio-provider-parity-ladder.md`) had dead
  links into both deleted files; devlog entries linking to the same paths
  were left alone (historical record, expected to reference
  now-superseded state — see `llm-collab`'s "Living Documentation" vs.
  point-in-time-journal distinction).

## Open Questions

- None new. (The promoted item's own file has none — it's implementation,
  not design.)

## References

- `.claude/todo.md` — the cleared tactical list
- `.claude/todo.kb/2026-07-12-000-AI-Studio--thread-per-turn-createTime-into-splat-basenames.md`
  — the promoted item
- `design.kb/040-design.kb/provider-plugin-model.md`,
  `.claude/todo.kb/2026-06-20-000-aistudio-provider-parity-ladder.md` —
  dead-link fixes
- `devlog/CLAUDE.md` — also fixed a stale `llm-collab-devlog -C ../`
  instruction found while trying to use it for this entry: the script
  hardcodes `docs/dev/devlog/` and cannot target this incubator's bare
  `devlog/`. Verified broken by direct reproduction; documented as manual
  creation instead.
