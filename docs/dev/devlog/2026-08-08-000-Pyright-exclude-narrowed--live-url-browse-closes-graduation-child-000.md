# Devlog: 2026-08-08 — Pyright exclude narrowed; live url-browse closes graduation child 000

## Focus

Follow-through from the user's review of the 2026-08-07 graduation pass:
narrow the pyright exclude they disagreed with, and run the live
url-browse verification that was the last open criterion on graduation
child 000 (module-shape refactor).

## What landed

- **72fd02f** — pyright `exclude` narrowed: `**/docs` replaced by
  `docs/dev/reference-implementations` only.
- Live url-browse verification: `chatfs-claude-conversation-url-browse
  --cache trash/live-cache/claude https://claude.ai/chat/00bd72f3-…`
  (a conversation known from the demo fixtures), user driving the
  browser. Full pipeline green: capture → pluck → splat (101 messages) →
  render (102 turns); contract layout on disk (`.chat/`, `.data/`
  exhaust with `cdp.jsonl.d/` scratch, `Created=` view symlink,
  `.chat/$UUID/.data` link), no `.tmp`/`.fail` leftovers. Closes child
  000's last criterion — children 000/001/002 of the graduation umbrella
  are now all done; 003 (bin crate + mount MVP) is the frontier.

## Decisions

### Only vendored code is pyright-excluded; our scripts stay red

**Rationale:** The 2026-08-07 pass hid all of `docs/` to get a clean
repo-root run. User: exclusion is for third-party code we don't own
(`reference-implementations`); our own exploration scripts
(aistudio-schema, fork-representation) stay checked, and there is no
requirement to fix pre-existing issues — leave them failing, visible, as
future work. The 3 surviving errors are enumerated in the root todo's
Deferred section; HACKING.md warns that repo-root `basedpyright` is
expectedly non-zero.
**Alternatives considered:** blanket `**/docs` (rejected: hides our own
code); fixing the 3 errors now (rejected: not this session's work, and
"fix everything you see" scope-creep is exactly what the deferred list
is for).

## Conventions Established

- A checker's baseline may stay red on purpose: suppressing pre-existing
  errors to manufacture a green run is worse than a tracked, visible
  failure list.

## Open Questions

- (none — child 000's live-verification question is what this session
  answered)

## References

- `docs/dev/devlog/2026-08-07-000-chatfs-cli-graduation-lands--promotion--entry-points--required---cache--docs-re-cut.md`
  — the pass this session follows through on
- `.claude/todo.kb/2026-07-13-000-graduation-and-integration.md` —
  umbrella state after this session
- `docs/how-to-chatfs.md` — the invocation the live run exercised,
  verbatim
