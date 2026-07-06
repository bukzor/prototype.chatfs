# Devlog: 2026-07-05 — chatfs-mockup-chatgpt: extract shared chatfs_layout.py

## Focus

Land the extraction planned in
`.claude/todo.kb/2026-05-11-001-shared-code-among-providers.md` and
`~/.claude/sessions.kb/provider-code-reuse-stutter-step.md`: with three
providers' `chatfs_<provider>_layout.py` sitting side by side
(chatgpt/claude/aistudio), factor the verbatim-shared parts into
`chatfs_layout.py`.

## Decisions

### Shared set vs. 3-line adapter

`DATA_DIR_NAME`, `safe_filename`, `_iso_offset`, `chat_dir_for`,
`data_dir_for`, `resolve_chat_dir`, `_purge_view_symlinks`, and
`place_meta`'s body were byte-for-byte identical across all three —
moved verbatim. `time_dir_for` now takes an already-parsed, tz-aware
`datetime` instead of a provider's raw wire-format timestamp; each
provider keeps a 3-line `_created()` doing that parse (chatgpt's
str|float, claude's ISO string, aistudio's int-string). Each provider's
`place_meta` shrank to a one-line wrapper pulling its own key names
(id/title/create_time vs uuid/name/created_at) and delegating to the
shared function.

**Rationale:** this is exactly the seam the third provider (aistudio)
exposed per the stutter-step session's rule-of-three analysis — the
adapter surface is 3 fields, not a larger interface.

### Unify the empty-title fallback into chatgpt's place_meta

chatgpt's `place_meta` lacked the `title or id` fallback that claude
and aistudio already had; an empty title would have collapsed the view
symlink onto `view_dir` itself. Unified as part of sharing one
`place_meta` body, confirmed with the user first since it's a behavior
change (not just a move).

**Alternatives considered:** special-case chatgpt to keep its old
(fallback-less) behavior — rejected; the fallback is strictly safer and
the divergence looked like an oversight, not an intentional choice.

### Lib home: incubator-local, not `packages/chatfs-core/`

Resolves the open question in `2026-05-11-001-shared-code-among-providers.md`.
Decided incubator-local — no packaging work until an actual
second-repo consumer exists.

## Conventions Established

- `place_meta`'s `item` parameter type is `Mapping[str, object]`, not
  `Mapping[str, JsonValue]` — pyright rejects passing a `TypedDict` as
  `Mapping[str, JsonValue]` (variance: `TypedDict` isn't a subtype of
  `Mapping[str, X]` for any `X` narrower than `object`). Fine here since
  `item` is only ever serialized (`json.dumps`), never read field-by-field
  after the identity fields are pulled out.

## Open Questions

- Land chatgpt fork-fact notation parity via the now-shared layout (the
  concrete parity-gap payoff this stutter-step was chasing) — next.

## References

- `.claude/todo.kb/2026-05-11-001-shared-code-among-providers.md`
- `~/.claude/sessions.kb/provider-code-reuse-stutter-step.md`
- Verified: pyright clean on `chatfs_layout.py` +
  `chatfs_{chatgpt,claude}_layout.py` (aistudio's pre-existing
  `index_item(doc: dict)` warnings untouched); idempotent re-run of the
  new `place_meta` against live `chatfs.demo/` data for all three
  providers (symlink count/target unchanged, `git status` clean);
  all 14 consumer scripts import without error.
