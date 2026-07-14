---
why:
  - unix-composability
---

# CLI Subcommand Dispatcher (git-style)

`chatfs <words…>` resolves to `chatfs-<words-joined-with-dashes>` on
`$PATH` and execs it, the way git dispatches `git foo` to `git-foo`.
Language-agnostic by construction: the kebab commands are Python entry
points today, the dispatcher lives in the Rust `chatfs` binary
(`040-design.kb/package-division.md`), and neither needs to know about the
other beyond the naming convention (`040-design` cli-command-shape, at its
owning package). Shell autocomplete over the discovered `chatfs-*` family
rides along.

Pure human ergonomics — every command remains directly invocable by its
kebab name, so this can be punted indefinitely. Pick it up when typing
kebab names grates.
