# Devlog: 2026-07-14 — Path-ownership contract v1 lands; data scratch dot-d convention decided

## Focus

Session start picked up the 2026-07-13 graduation-and-integration umbrella
(`.claude/todo.kb/2026-07-13-000-graduation-and-integration.md`) and took
child 002 (path-ownership-contract-v1) — two other agents took 000
(module-shape-refactor) and the incubator's atomic-regeneration todo
concurrently in the same working directory.

## Decisions

### `docs/dev/technical-policy.kb/path-ownership.md` written (child 002 done)

A descriptive `.chat/$UUID/` path-ownership contract: `.data/` contract
files vs. derived members (`messages/`, `conversations/`, `chat.md`) vs.
the view-tree symlinks vs. the not-yet-built daemon's control plane,
each `[!TODO]`-marked where aspirational. Checked off in the umbrella and
in the child task file.

**Rationale:** fills the gap `black-box-decomposition.md` leaves open
(names the component seam, not which paths belong to whom); scoped per
the task's own instruction to name owners/roles, never scripts or CLI
args, so the doc survives 000's coming renames.

**Alternatives considered:** none for the doc's existence — it was
tasked. The first draft did name providers (ChatGPT/Claude/AI Studio)
in three table rows to explain real divergence (AI Studio's raw→massage
step, ChatGPT-only `conversations/`); user corrected this as a mistake
mid-review — a cross-cutting policy doc should describe the general
shape, not one provider's implementation detail. Rewritten generically
(see next decision).

### `.data/` scratch convention: reserve `X.d/` per top-level contract name

For any fixed top-level name `X` in `.data/` (`meta.json`,
`conversation.json`, `cdp.jsonl`), the sibling `X.d/` is reserved for
scratch/intermediate files related to producing or checking `X`.
Nothing outside a stage may depend on a scratch file's name or
presence. Not yet implemented — spun off as its own todo (see below).

**Rationale:** the provider-naming fix above still needed to explain
*where* things like a pre-normalization pluck or an incidental
cross-check dump live, without naming which provider needs them. `X.d/`
answers that structurally: reservation is free (costs nothing for
contract files that never need scratch), `ls`-legible by position (same
shape as `.chat/` vs. the view tree, one level up), and precedented
(`/etc/apt/sources.list.d/`).

**Alternatives considered:** an initial proposal reserved
`.data/<stage>/` per pipeline stage (capture, massage, ...) — rejected
by the user in favor of `X.d/`. Process-scoped scratch dirs require
inventing and agreeing on stage names in the storage layer; artifact-
scoped `X.d/` is purely mechanical off the contract name itself, needs
no stage vocabulary, and generalizes past `.data/` to any top-level
contract name anywhere in the tree.

### Implementation spun off as its own orthogonal todo

`docs/dev/design-incubators/chatfs-cli-mockup/.claude/todo.kb/2026-07-14-000-Migrate-data-scratch-files-into-dot-d-sibling-directories.md`
— moves the two real ad hoc top-level files (a pre-normalization pluck,
an incidental cross-check dump) under their matching `X.d/`, updates
`chatfs_layout.py`'s docstring and one design doc, and closes
path-ownership.md's `[!TODO]`.

**Rationale:** user asked directly whether it depends on or blocks
anything else. Traced against every umbrella child: no `blocked-by`
edge either direction — it doesn't touch import structure (000),
packaging/CLI surface (001), the Rust side (003/004), or the
atomic-regeneration swap boundary (`.data/` is explicitly *input* to
that swap, never the atomically-swapped surface). Noted as cheapest to
land alongside 000's file-touching pass, but not required to.

## Conventions Established

- Cross-cutting `technical-policy.kb/` docs name components/roles, never
  providers or specific scripts — provider divergence is described
  generically (e.g. "produced only when the source has branches to
  represent") so the doc doesn't leak one provider's implementation
  detail into a contract every provider is bound by.
- When a storage-layer convention needs a "this is scratch, ignore it"
  marker, prefer reserving a name mechanically off the thing it scratches
  for (`X.d/` beside contract file `X`) over inventing a parallel
  process/stage vocabulary in the storage layer.

## Open Questions

- None for child 002 itself (deliberately descriptive v1, per its task
  file). The `X.d/` migration todo has none either — mechanical rename,
  same shape at every call site.

## References

- `.claude/todo.kb/2026-07-13-000-graduation-and-integration.kb/2026-07-13-002-path-ownership-contract-v1.md`
  — the child task, checked off.
- `docs/dev/technical-policy.kb/path-ownership.md` — the doc itself.
- `docs/dev/design-incubators/chatfs-cli-mockup/.claude/todo.kb/2026-07-14-000-Migrate-data-scratch-files-into-dot-d-sibling-directories.md`
  — follow-up implementation todo.
- Unrelated finding, not fixed: `2026-07-13-000-Atomic-chat-dir-regeneration---stage-and-rename--never-rewrite-in-place.md`
  fails `llm.kb-validate` (`cost-benefit-sweh.timebox.confidence: firm`
  not in the schema's enum) — predates this session, out of scope.
