---
managed-by: Skill(llm-subtask)
status: deferred
cost-benefit-sweh:
  timebox:
    "@value": 0.5  # SWEh worth exploring before promoting or abandoning
  benefit-2w:
    "@value": 0.5  # low while docstring convention holds; rises with contributor count
---

# Purity gate: AST scan for shell-only imports

## The Idea

Mechanically enforce the `chatfs` purity invariant ("everything outside
`shell/` is pure, except `main()`") decided 2026-07-19 with the
module-shape refactor
(`todo.kb/2026-07-13-000-graduation-and-integration.kb/2026-07-13-000-module-shape-refactor.md`,
2026-07-19 amendment). A ~40-line AST-scanning test, no new dependency,
asserting for every non-`shell/`, non-test module:

- no top-level import from a denylist ({os, sys, subprocess, shutil,
  tempfile, fcntl, signal, io}) and no top-level import of
  `chatfs.shell` — such imports may appear only inside `def main`
  (the inline-import convention is the enforcement seam: gating
  top-level imports only makes an inline `import subprocess` in
  `main()` the declared escape hatch);
- optionally, no attribute calls from a name denylist (`.mkdir`,
  `.write_text`, `.open`, `.read_text`, `.symlink_to`, `.rename`,
  `.unlink`, builtin `open`) outside `main()` — closes the
  `pathlib`-reader gap that import-gating alone can't see
  (`load_turns`-style fs reads).

## Potential Benefits

- Purity regressions caught at test time instead of review time.
- The denylist doubles as executable documentation of the invariant.

## Open Questions / Unknowns

- Is the attribute-call scan's false-positive rate acceptable (e.g.
  non-Path `.open()` on other objects)?
- Should tests be exempt wholesale or only `*_test.py` by name?

## Exploration Notes

Deliberately deferred 2026-07-19 (user): docstrings in
`chatfs/__init__.py` and `chatfs/shell/__init__.py` stating the
invariant are the ~90% solution; a mechanical gate isn't worth its
weight while the convention is fresh and the contributor set is one.

## Next Steps (if pursuing)

- [ ] Trigger: a purity violation slips past review into main — promote
      this to a todo.kb entry and write the import-scan half first.

## Lifecycle

**Status:** Exploring
