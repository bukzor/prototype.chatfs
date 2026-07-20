# Devlog: 2026-07-20 — claude family edit pass: package imports + pure/shell split

## Focus

Landed the edit pass for `todo.kb/2026-07-13-000-graduation-and-
integration.kb/2026-07-13-000-module-shape-refactor.md`'s "move one
provider family end-to-end" step: claude family + the shared core it
depends on. Real `chatfs.` package imports throughout, replacing every
sibling-import (`chatfs_layout`, `chatfs_json`, etc.) the 2026-07-19
`git mv` left broken (that commit relocated files with zero content
edits).

## What landed

- **Shared core split**: `chatfs/layout.py` trimmed to pure path
  vocabulary; new `chatfs/pluck.py` (CDP-filter skeleton); new
  `chatfs/shell/capture.py` + `chatfs/shell/place.py` (the impure
  halves — browse/capture/pluck-to-disk and place_meta/resolve_chat_dir/
  view-symlink maintenance).
- **Claude provider split**, matching: `provider/claude/layout.py`
  trimmed to pure claude-shaped knowledge (`created_at`, `url_for`,
  `uuid_from_url` — the latter two consolidated out of duplicated
  copies previously in `url_browse.py`/`url_render.py`); new
  `provider/claude/pluck.py` (URL regexes + pluck functions).
- **New `chatfs/paths.py`**: `INCUBATOR_ROOT` + `demo_root(provider)`,
  the shared anchor every leaf entry point's demo-tree path
  (`chatfs.demo/<provider>`) is built from. Necessary because
  file-relative path composition (`Path(__file__).parent / ...`) only
  worked when these scripts were flat incubator-root siblings; nested
  under `provider/<name>/...` it silently resolves to the wrong
  directory instead of erroring, so it needed a single well-tested
  anchor rather than per-file arithmetic.
- **Orchestrator delegation stays subprocess-based**
  (`path_browse`/`url_browse`/`url_render` → `path_render` →
  `splat`/`render`, via `python -m chatfs.provider.….X`) — by design,
  not a stopgap; see `design.kb/040-design.kb/driver-model.md`'s
  decision record: this keeps the CLI-shaped calling convention
  actually exercised by normal operation, and caps coupling between
  pipeline stages to argv/stdio rather than shared Python internals.
  Each stage still gained its own importable, independently-testable
  driver function (`splat.splat`, `render.render_chat_dir`,
  `path_render.path_render`) separate from `main()` — useful on their
  own even though the standard delegation chain calls the CLI form, not
  the function. `chatfs.shell.sh.run` gained a `cwd` parameter, since
  `python -m` resolves the `chatfs` package via the interpreter's cwd,
  not the invoking script's directory.
- **Purity convention honored throughout**
  (`chatfs/__init__.py`/`chatfs/shell/__init__.py`): impure stdlib
  imports (`sys`, `shutil`, `subprocess`) are inline within whichever
  function actually needs them, never at module top level, outside
  `shell/`.
- **Test files split to mirror** the production split:
  `layout_test.py`/`pluck_test.py`/`shell/capture_test.py`/
  `shell/place_test.py`/`paths_test.py`. `atomic_test.py`/
  `locks_test.py` and their subprocess-spawned `child_*.py` helpers
  updated to the post-move directory names and an incubator-root
  `PYTHONPATH` so their own `chatfs.shell.*` imports resolve.

## Verification

pytest 79/79 (claude family + shared core scope —
`--ignore=chatfs/provider/aistudio --ignore=chatfs/provider/chatgpt`;
those two providers are untouched, still red as expected, their own
edit pass is next). basedpyright 0 errors/0 warnings on the same scope.

## Open Questions

Carried forward from the parent todo: sweep chatgpt/aistudio against
this session's template; decide chatgpt-splat's external-vs-folded-in
home during that sweep; update the incubator README's "Run it" section
once the full sweep lands (not per-family, per the plan).

The live end-to-end run (module-shape-refactor's Success Criteria) is
deliberately not attempted this session — held for an explicit,
asked-first pass rather than folded into routine verification.
Worth knowing going in: `provider/claude/index/browse.py` takes no
arguments and its `main()` performs a real `browse()` (live
`har-browse` capture) immediately on invocation — there is no
argument-gated usage path to fall back on, unlike every other entry
point in this family. Treat any direct invocation of it as a live
action against the real site, never as a smoke test.

## References

- `todo.kb/2026-07-13-000-graduation-and-integration.kb/2026-07-13-000-module-shape-refactor.md`
- `design.kb/040-design.kb/driver-model.md`
- `chatfs/__init__.py`, `chatfs/shell/__init__.py`
- `chatfs/layout.py`, `chatfs/pluck.py`, `chatfs/paths.py`,
  `chatfs/shell/capture.py`, `chatfs/shell/place.py`, `chatfs/shell/sh.py`
- `chatfs/provider/claude/layout.py`, `chatfs/provider/claude/pluck.py`
