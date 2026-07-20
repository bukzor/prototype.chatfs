---
why:
  - unix-composability
  - pipeline-composability
---

# Driver Model — Pipe and Delegation as Thin Drivers Over One Library

Index flow is user-composed by pipe (`chatfs_chatgpt_index_browse.py |
chatfs_chatgpt_index_splat.py`); conversation flow is nested delegation
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

`chatfs_layout.py::capture()`, built on its `browse()`/`pluck()`
primitives, is the first instance of this: every provider's
`url_browse`/`path_browse` delegation orchestrator, and every
incidental-index pluck call, now calls these shared functions rather
than each reimplementing `subprocess.run(["har-browse", url],
stdout=...)` inline or shelling out to a `.jq` filter. A provider's own
`capture()` wrapper (`chatfs_claude_layout.capture`, etc.) is a thin
partial application — it supplies the provider's pluck function and
output filename, nothing else. `run_pluck()` (subprocess-to-a-script)
still exists for the one case that's a genuine external script rather
than an in-process generator: AI Studio's massage stage.

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
