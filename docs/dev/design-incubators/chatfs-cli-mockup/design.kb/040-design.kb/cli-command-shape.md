---
why:
  - unix-composability
  - pipeline-composability
last-updated: 2026-08-07
---

# CLI Command Shape

Pipeline commands are named as if they were subcommands of a future
`chatfs` CLI: noun-then-verb, with an explicit locator sub-noun where
the same action accepts multiple input shapes. Since 2026-08-07 they
are installed entry points (`packages/chatfs-cli`'s
`[project.scripts]`), no longer loose scripts; the naming scheme
promoted unchanged.

## Partition vocabulary

- **Provider** — outermost grouping for per-provider script families.
- **Noun** — an artifact the pipeline manipulates.
- **Verb** — an operation applied to a noun.
- **Sub-noun (locator)** — disambiguates input shape (e.g. `url` vs
  `path`) when a verb accepts multiple. Sits between noun and verb in
  the command path (e.g. `conversation url browse`).
- **Bare-verb leaf** — stdio-only entry point that emits data on
  stdout from prepared inputs.
- **Orchestrator form** — locator-prefixed command that arranges
  capture, splat, and placement around a bare-verb leaf.

## Why explicit locators

A verb that quietly accepts both a URL and a directory path is harder
to read in a pipeline and harder to shell-complete than two separate
commands. The few extra keystrokes (`url browse` vs `browse`) buy
clarity.

## Naming conventions

Subcommand paths map to commands on `$PATH` with `-` separators
(`chatgpt conversation url browse` →
`chatfs-chatgpt-conversation-url-browse`). Python module paths express
the same partition as dots, with `_` inside a single segment:
`chatfs.provider.chatgpt.conversation.url_browse` — including
provider-internal helpers with no `$PATH` command of their own
(e.g. `chatfs.provider.chatgpt.pluck`).

---

Per-partition rationale lives in `cli-command-shape.kb/`, keyed by
partition prefix (`noun=index.md`, `verb=splat.md`,
`noun=conversation.kb/locator=url.md`, etc.). See the kb's `CLAUDE.md`
for partition-key conventions and the promotion rule.
