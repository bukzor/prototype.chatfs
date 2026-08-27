---
why:
  - ../../../../docs/dev/design.kb/020-goals.kb/unix-composability.md
  - ../../../../docs/dev/design.kb/030-requirements.kb/pipeline-composability.md
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
- **Bare-noun driver** — the noun with no verb: runs that noun's whole
  pipeline end to end with default arguments (`chatfs-claude-index` is
  `index browse | index splat`).

## Why explicit locators

A verb that quietly accepts both a URL and a directory path is harder
to read in a pipeline and harder to shell-complete than two separate
commands. The few extra keystrokes (`url browse` vs `browse`) buy
clarity.

## Why a bare-noun driver

Explicit stages are the honest surface -- each one is separately
runnable and separately debuggable -- but a user who just wants their
index refreshed should not have to name the cache twice and remember
which two verbs compose. The bare noun is that default: the shortest
name in the family does the whole job.

It also lands first in shell completion. `chatfs-claude-index<TAB>`
offers `chatfs-claude-index` ahead of its own `-browse`/`-splat`
leaves, so the completion list opens with the command that finishes the
task rather than with a stage.

Naming stays consistent with the noun-then-verb scheme by treating the
absent verb as "all of them, in order". A noun earns a driver only when
its stages compose into one obvious default; where a noun's verbs are
genuinely alternatives (`conversation` browse vs render vs trash),
there is no default to name and no bare-noun command exists.

## Naming conventions

Subcommand paths map to commands on `$PATH` with `-` separators
(`chatgpt conversation url browse` →
`chatfs-chatgpt-conversation-url-browse`). Python module paths express
the same partition as dots, with `_` inside a single segment:
`chatfs.provider.chatgpt.conversation.url_browse` — including
provider-internal helpers with no `$PATH` command of their own
(e.g. `chatfs.provider.chatgpt.pluck`).

A bare-noun driver's module path lands on the noun's package rather
than a module inside it, so its code lives in that package's
`__main__.py` (`chatfs.provider.chatgpt.index.__main__`). This keeps
`__init__.py` empty as the style guide requires, and makes `python -m
chatfs.provider.chatgpt.index` name the driver -- the same `python -m`
form every orchestrator already uses to invoke a stage.

---

Per-partition rationale lives in `cli-command-shape.kb/`, keyed by
partition prefix (`noun=index.md`, `verb=splat.md`,
`noun=conversation.kb/locator=url.md`, etc.). See the kb's `CLAUDE.md`
for partition-key conventions and the promotion rule.
