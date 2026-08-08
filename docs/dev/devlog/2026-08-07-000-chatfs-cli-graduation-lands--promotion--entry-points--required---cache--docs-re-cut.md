# Devlog: 2026-08-07 — chatfs-cli graduation lands: promotion, entry points, required --cache, docs re-cut

## Focus

Close graduation child 001 (promote the pipeline to `packages/chatfs-cli/`):
the code was already package-shaped in place (child 000's edit passes), but
its usage was still tied to the incubator directory and no real CLI
integration existed despite real packaging.

## What landed

Four code commits, then this docs/bookkeeping pass:

- **a92f4a1** — rename `packages/chatfs/` → `packages/chatfs-cli/`
  (distribution `chatfs-cli`, import package stays `chatfs`); legacy
  `layer/` stub deleted.
- **87db8ca** — `git mv` the incubator's `chatfs/` package to
  `packages/chatfs-cli/lib/chatfs/`, tests riding along.
- **0863b1a** — 25 `[project.scripts]` entries, one
  `chatfs-<provider>-<noun>-<verb>` kebab command per stage
  (cli-command-shape.md's mapping); the stub `chatfs` script dropped —
  that name stays reserved for the future dispatcher (package-division.md).
- **75ff707** — untie every entry point from the incubator directory:
  required `--cache <dir>` on url-addressed and index leaves, module
  constants (`ROOT`/`OUT_DIR`/`CDP`) and every `cwd=INCUBATOR_ROOT` hack
  deleted, pyright `executionEnvironments` workaround replaced by a plain
  `exclude` (incl. `**/docs`). Verified: pytest 143/143, basedpyright 0
  errors from repo root, url-render from a foreign cwd sha256-identical
  across runs.

This pass: how-to re-cut around the installed commands; package README
written (absorbing the incubator README's stage walkthrough); incubator
README made historical; incubator todos re-homed to
`packages/chatfs-cli/.claude/`; path-ownership.md and package-division.md
`[!TODO]`s unwrapped; child-001 + umbrella checkboxes; repo-wide reference
sweep (HACKING.md, har-browse CLAUDE.md, aistudio-schema discourse
pointer, module docstrings' `../aistudio-schema` paths).

## Decisions

### Cache root: required `--cache <dir>`, no default (XDG reverted)

**Rationale:** Mid-session we added a platformdirs/XDG default cache root;
the user flagged it as violating design contract, and the design docs
agree: path-ownership.md's own `[!TODO]` specified "a required argument
everywhere, with no baked default, so the daemon can point arbitrary
mounts at arbitrary cache roots", and the graduation planning devlog
called XDG defaults "deferrable ergonomics". platformdirs is gone;
url-addressed and index commands take `--cache <dir>`, path-addressed
commands infer the root from their path argument.
**Alternatives considered:** positional cache argument (rejected: ordering
ambiguity beside the URL positional; a flag can later relax to optional
without breaking invocations); XDG default (rejected as above).

### Completed todos deleted at re-homing, not carried

The atomic-regeneration todo was fully closed (all criteria checked,
devlogged in the incubator's `2026-07-18-002-…`), so it was deleted per
`todo clear` rather than moved. The three live todo.kb files and todo.md
carried over with relative links rewritten (incubator-relative paths →
repo-root-relative).

### `trash/` is a cache-root contract name

url-trash moves a chat dir + its view symlinks to the cache root's own
`trash/$TIMESTAMP/` (same filesystem ⇒ rename; the cache need not live in
any repo). Recorded in path-ownership.md alongside `.chat/`/`.data/`/the
view tree. While documenting it, found and fixed a real inconsistency:
`_purge_view_symlinks` skipped `.chat/`/`.data/` but not `trash/`, so
re-capturing a previously-trashed chat would have stripped view symlinks
out of the preserved trash artifact. Two-line fix + regression test in
`place_test.py` (mutation-verified), 54/54 shell tests green.

## Conventions Established

- Docs split: `docs/how-to-chatfs.md` is user-facing (commands, layout,
  failure modes); `packages/chatfs-cli/README.md` owns the stage-by-stage
  anatomy; the incubator README is a historical note pointing at both.
- `chatfs.demo/<provider>` fixtures stay in the incubator; the how-to
  points `--cache` at them for offline render exercise.

## Open Questions

- Child 000 retains one open criterion: a live url-browse verification
  (ask-first browser/network action, not yet run in any edit-pass session).

## References

- `.claude/todo.kb/2026-07-13-000-graduation-and-integration.kb/2026-07-13-001-promote-to-packages-chatfs-cli.md`
- `docs/dev/technical-policy.kb/path-ownership.md` — cache-root and
  `trash/` contract as now recorded
- `docs/dev/design.kb/040-design.kb/package-division.md`
- `docs/dev/devlog/2026-07-13-000-graduation-and-integration-planning.md`
