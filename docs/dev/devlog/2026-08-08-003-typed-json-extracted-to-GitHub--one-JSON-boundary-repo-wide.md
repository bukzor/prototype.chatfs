# Devlog: 2026-08-08 — typed-json extracted to GitHub; one JSON boundary repo-wide

## Focus

Collapse the repo's six stdlib-`Any` laundering points (in three competing
styles) toward one. User review of 2026-08-08-001's cast policy asked why
four `cast(JsonValue, json.loads(...))` sites remained instead of one central
policy contradiction, and recalled a dormant `~/repo/github.com/bukzor/typed-json`.

## What landed

- **`bukzor/typed-json` pushed to GitHub** (was a local-only repo, one
  commit, no remote; the PyPI name is free but unpublished). Its `loads`/
  `load` cast under the stdlib default-decoder guarantee; its deep
  `is_json_*` TypeGuards are reserved for values of unknown origin.
- **`chatfs-cli` adopts it**: `chatfs/json.py` deleted; 26 files swapped
  `chatfs_json`/`chatfs.json` → `typed_json` mechanically. This removed the
  O(n) verify-on-every-load walk and its 7 ignore comments.
- **Exploration scripts adopt it** (`body-shape.py`, `extract-bundles.py`,
  `investigate-forks.py`): local `JsonValue` aliases and boundary casts
  deleted; shebang is now `#!/usr/bin/env -S uv run --script` with PEP 723
  inline metadata sourcing typed-json from GitHub, so direct `./script.py`
  execution still works with no repo venv.
- **`rosetta/convert.py`**: the repo's last ignore comment
  (`# pyright: ignore[reportAny]` in `load_json`) became an overt
  `cast(object, json.load(fp))` — same zero-trust contract, visible to the
  `grep cast(` audit.
- **`docs/dev/aistudio-schema/pyproject.toml` deleted** (with its uv.lock
  and .venv): it existed solely to run basedpyright locally, root is
  canonical since 2026-08-08-001, and it couldn't resolve `typed_json`.
- Verified: pyright 0/0, 144 tests pass, and all three scripts produce
  byte-identical output on real fixtures (aistudio CDP capture, claude
  conversation.json from chatfs.demo).

## Decisions

### One laundering boundary per program; the library is the program for packages

**Rationale:** The cast asserts "this parser invocation yields this shape",
so its floor is one per (program × parser config). Packages share the
typed-json boundary through a normal dependency. End state: typed-json's
`loads` upstream is *the* default-decoder contradiction;
`chatgpt_export/json.py` keeps its own cast because `parse_float=Decimal`
is a different invariant (its `JsonValue` has `Decimal`, no `float` —
outside typed-json's contract); `convert.py` keeps its zero-trust
`cast(object, ...)`, which claims nothing.
**Alternatives considered:** A shared helper under docs/ — recreates the
rosetta extraPaths problem; forcing Decimal or float repo-wide — falsifies
one side's types.

### GitHub git-dependency over vendoring

**Rationale:** A vendored `packages/typed-json/` copy (built first) would
drift from the canonical repo. User preferred a GitHub reference; precedent
already in-tree (`basedpyright-as-pyright` git source). uv.lock pins the
rev. Scripts reference the same git source in PEP 723 blocks, keeping them
single-file and repo-independent.
**Alternatives considered:** workspace member (drift, two copies); PyPI
(not yet published — the natural next step, after which the sources tables
can be dropped).

## Conventions Established

- New JSON ingestion anywhere in the repo: `from typed_json import ...`.
  Never a new local alias/cast; nonstandard decoder configs get their own
  named boundary module with one cast and the invariant stated.
- Standalone scripts that need a dependency: PEP 723 inline metadata +
  `#!/usr/bin/env -S uv run --script`, not an incubator venv.

## Follow-up

- The cast policy is promoted to
  `technical-policy.kb/any-laundering-boundaries.md` — the durable statement;
  this entry and 2026-08-08-001 are its history.
- User is publishing typed-json to PyPI out-of-repo; once it lands, drop the
  `[tool.uv.sources]` git pins here and in the script metadata blocks.
- TypeGuard → TypeIs for typed-json's guards: filed at typed-json scope
  (`.claude/todo.md` in that repo).

## Open Questions

-

## References

- 2026-08-08-001 — the cast-policy review this answers
- <https://github.com/bukzor/typed-json>
