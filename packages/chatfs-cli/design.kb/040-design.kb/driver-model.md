---
why:
  - ../../../../docs/dev/design.kb/020-goals.kb/unix-composability.md
  - ../../../../docs/dev/design.kb/030-requirements.kb/pipeline-composability.md
---

# Driver Model — Pipe and Delegation as Thin Drivers Over One Library

Index flow is user-composed by pipe (`chatfs-chatgpt-index-browse |
chatfs-chatgpt-index-splat`); conversation flow is nested delegation
(`url_browse` calls `path_render`, which calls splat and render as
subprocesses). The two surfaces look like competing philosophies, but
neither should give way to the other: the resolution is that both are
thin drivers over the same importable stage functions, not two
independent implementations of capture/pluck/splat/render logic.

## The decision

A pipeline stage (browse, pluck, splat, render) is written once as an
importable Python function, living in a shared or provider module. The
pipe surface (a shell one-liner joining leaf scripts with `|`) and the
delegation surface (an orchestrator script calling the next stage
directly) both call into that same function — through a subprocess
invocation of the leaf script, or, where in-process calling is cheap
enough, a direct import. Neither surface owns the logic; both address
it.

This is why choosing between "make conversation flow pipe-composed
like index flow" and "make index flow delegate like conversation flow"
was a false choice: the shape difference between the two flows is
real (index has one consumer-composed stream of pages; conversation
has multiple named output files with no single stream to plumb — see
`stdio-pipeline-shape.md`), but the *logic* underneath either shape
should still be shared.

## What's landed

`chatfs.shell.capture.capture()`, built on its `browse()`/`pluck()`
primitives, is the first instance of this: every provider's
`url_browse`/`path_browse` delegation orchestrator, and every
incidental-index pluck call, now calls these shared functions rather
than each reimplementing `subprocess.run(["har-browse", url],
stdout=...)` inline or shelling out to a `.jq` filter. The provider
`capture()` wrappers have since dissolved into leaf `main()`s that pass
the provider's pluck function and output filename to `capture()`
directly (the 2026-07-19 purity split). `run_module()` (subprocess
`python -m`) still exists for the one stage that's a genuine separate
command rather than an in-process generator: AI Studio's massage stage.

The index flow's pipe now has a driver of its own —
`chatfs-<provider>-index`, the bare-noun form
(`cli-command-shape.md`) — but this does not move the index flow from
the pipe surface to the delegation surface. The driver *is* the pipe:
it spawns `python -m …index.browse` and `python -m …index.splat` and
joins their stdio with an OS pipe (`chatfs.shell.sh.pipe`), so the
stages still address each other only through argv and stdio, exactly
as when the user types the `|`. What it saves is the second
`--cache` and the need to remember which two verbs compose, not a
process boundary. `pipe()` raises on either stage's non-zero exit —
`pipefail`, not the shell's last-stage-only default — so a failed
browse can't be swallowed by a splat that happily reads zero pages.

## Decided against: converting splat/render delegation to in-process calls

Splat and render are each factored into an importable, testable pure
function (`chatfs.provider.claude.conversation.splat.splat`,
`...render.render_chat_dir`; `path_render.path_render` the same, one
level up) — but the orchestrators that chain them
(`path_browse`/`url_browse`/`url_render` → `path_render` → `splat`/
`render`) call them as subprocesses (`python -m chatfs.provider.….X`),
not in-process imports, and stay that way deliberately (settled
2026-07-20, discussed with user, after a same-session attempt at the
in-process conversion was reverted).

This is narrower than `capture()`'s case above: `capture()` composes
`browse()`/`pluck()`, primitives that were never separate CLI leaf
scripts to begin with, so calling them in-process was never a choice
between two working alternatives. Splat/render/path_render *are*
separate CLI leaf scripts, each independently invocable, and that's
exactly the property worth protecting: forcing every leaf-to-leaf
handoff through argv/stdio (never a direct Python call across a script
boundary) means the CLI-shaped calling convention stays *exercised* by
the pipeline's own normal operation, not just theoretically available
and silently rotting the moment something faster is available in the
same process. It also caps how wide any two subsystems' coupling can
grow — a process boundary, not shared Python internals, so a change on
one side can never accidentally reach across into the other's
implementation details.

The importable functions still exist and are still the right shape —
tests call them directly, and a future caller that genuinely needs
in-process composition has them available. They're just not how the
leaf scripts talk to *each other*.
