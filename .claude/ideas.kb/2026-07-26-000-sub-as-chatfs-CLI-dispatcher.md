---
managed-by: Skill(llm-subtask)
status: open
cost-benefit-sweh:
  timebox:
    "@value": 1.0  # SWEh worth exploring before promoting or abandoning
  benefit-2w:
    "@value": 3.0  # SWEh value created over 2w if this pans out
---

# sub as chatfs CLI dispatcher

## The Idea

Provide the `chatfs` dispatcher command (the stub Python entry point was
dropped at graduation, 2026-08-07 — the name is reserved for a future
dispatcher per `package-division.md`) over `chatfs-cli`'s provider tree using
[juanibiapina/sub](https://github.com/juanibiapina/sub) -- a 1.3k-line Rust
dispatcher that turns a `libexec/` directory tree into a CLI with nested
subcommands, per-level help, completions, and argument validation.

A small generator emits `libexec/<provider>/<noun>/[<locator>/]<verb>` shims
(`exec python -m chatfs.provider.... "$@"`) with `# Summary:` / `# Usage:` /
`# Options:` magic comments extracted from each module's docstring -- single
source of truth. `bin/chatfs` is a 3-line sub invocation.

## Potential Benefits

Verified by dogfood (2026-07-26, chatfs-shaped probe tree):

- Mixed bare-leaf + orchestrator dirs (`conversation/render` beside
  `conversation/url/`) render correctly in help -- matches
  `packages/chatfs-cli/design.kb/040-design.kb/cli-command-shape.md`
  exactly.
- Magic comments in Python files (after shebang) produce polished leaf
  `--help`; clap-grade validation runs before the interpreter starts.
- Raw argv passes through unchanged, so existing argparse code needs no
  changes; `_CHATFS_ARGS` (shlex-parseable) is available when wanted.
- Subcommand completion at every depth in ~6ms, no Python launch.
- stdio pipelines (`index browse | index splat`) pass through untouched.
- Free: `_CHATFS_ROOT`, XDG `_CHATFS_CACHE`, symlinks-as-aliases,
  group docs via `README` with the same magic comments.

## Open Questions / Unknowns

- Distribution: `pip install chatfs` wants a Python entry point; sub is an
  external binary. Fine while prototyping (installed via cargo-built formula
  in `~/repo/github.com/bukzor/tap`); the tree + comment contract survive a
  later swap to an in-Python dispatcher.
- Wart: trailing `--help` fails at *group* level (`chatfs chatgpt --help`);
  bare dir or prefix form (`chatfs --help chatgpt`) works. PR-able upstream.
- Upstream is quiet (last substantive commit 2026-01). Depend-vs-fork
  decision tracked at `~/.claude/todo.kb/2026-07-26-000-Evaluate-sub--patch-upstream--hard-fork--or-write-my-own.md`.

## Exploration Notes

Probe tree preserved in this entry's `.d/` sibling
(`2026-07-26-000-sub-as-chatfs-CLI-dispatcher.d/`): run
`.d/bin/chatfs chatgpt conversation url browse --help` to see the contract
in action.
`cli-command-shape.md`'s "Naming conventions" section was updated
2026-08-07 for the installed kebab entry points; adopting sub would
rewrite it again (nested subcommands replacing the flat kebab names).

## Next Steps (if pursuing)

- [ ] Write the shim generator (docstring -> magic comments)
- [ ] Point `bin/chatfs` at the generated libexec tree
- [ ] Wire shell completion (`chatfs --completions`) into bash/zsh setup
- [ ] Rewrite `cli-command-shape.md` naming section for the decided shape

## Lifecycle

**Status:** Exploring
