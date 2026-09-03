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
promoted unchanged. The `provider` segment became explicit 2026-08-28,
having been dropped from the command name while present in the module
path all along.

## Partition vocabulary

- **Provider** — a named adapter, addressed under the `provider`
  partition (`provider claude …`). The segment is written, not elided:
  that is what keeps a command's kebab name equal to its module path,
  and it leaves the bare `<noun> <verb>` names free for the
  provider-dispatching forms.
- **Noun** — an artifact the pipeline manipulates.
- **Verb** — an operation applied to a noun.
- **Sub-noun (locator)** — disambiguates input shape (e.g. `url` vs
  `path`) when a verb accepts multiple. Sits between noun and verb in
  the command path (e.g. `conversation url browse`).
- **Bare-verb leaf** — stdio-only entry point that emits data on
  stdout from prepared inputs.
- **Orchestrator form** — locator-prefixed command that arranges
  capture, splat, and placement around a bare-verb leaf.
- **Dispatching form** — a command with no provider segment, which
  reads the provider off the locator it was given and runs the
  corresponding `provider` command. Only a verb whose argument is an
  *address* can have one: `conversation url browse` dispatches on the
  URL's host and `conversation path render` on the chat dir's cache
  segment, but `conversation splat` takes a `conversation.json` and an
  output dir — a file and a destination, not an address, and neither is
  required to sit in a cache at all. Inferring a provider from those
  would be sound only by coincidence.
- **Bare-noun driver** — the noun with no verb: runs that noun's whole
  pipeline end to end with default arguments (`chatfs-provider-claude-index` is
  `index browse | index splat`).
- **Fan-out driver** — a command with no provider segment that runs
  *every* provider's form of itself in turn (`chatfs-refresh`). Distinct
  from a dispatching form, which picks one provider from an address it
  was given; a verb taking no address can't dispatch, but it can still
  fan out. See `cli-command-shape.kb/verb=refresh.md`.

A verb may also apply to the `provider` partition itself, with no noun
between, when its object is that provider's whole cache rather than any
one artifact (`provider claude refresh`).

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

It also lands first in shell completion. `chatfs-provider-claude-index<TAB>`
offers `chatfs-provider-claude-index` ahead of its own `-browse`/`-splat`
leaves, so the completion list opens with the command that finishes the
task rather than with a stage.

Naming stays consistent with the noun-then-verb scheme by treating the
absent verb as "all of them, in order". A noun earns a driver only when
its stages compose into one obvious default; where a noun's verbs are
genuinely alternatives (`conversation` browse vs render vs trash),
there is no default to name and no bare-noun command exists.

## Naming conventions

Subcommand paths map to commands on `$PATH` with `-` separators
(`provider chatgpt conversation url browse` →
`chatfs-provider-chatgpt-conversation-url-browse`). Python module paths
express the same partition as dots, with `_` inside a single segment:
`chatfs.provider.chatgpt.conversation.url_browse` — every segment
appears in both spellings — including
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
