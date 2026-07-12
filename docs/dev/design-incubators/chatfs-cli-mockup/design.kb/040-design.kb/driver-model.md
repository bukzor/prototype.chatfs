---
why:
  - unix-composability
  - pipeline-composability
---

# Driver Model — Pipe and Delegation as Thin Drivers Over One Library

Index flow is user-composed by pipe (`chatfs_chatgpt_index_browse.sh |
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

`chatfs_layout.py::capture()` and `chatfs_layout.py::run_pluck()` are
the first instance of this: every provider's `url_browse`/`path_browse`
delegation orchestrator, and every incidental-index pluck call, now
calls these two shared functions rather than each reimplementing
`subprocess.run(["har-browse", url], stdout=...)` /
`subprocess.run([pluck_script], stdin=..., stdout=...)` inline. A
provider's own `capture()` wrapper (`chatfs_claude_layout.capture`,
etc.) is a thin partial application — it supplies the provider's pluck
script and output filename, nothing else.

> [!TODO]
> Splat and render stages are not yet unified the same way. Each is
> already factored into an importable, testable pure function (e.g.
> `chatfs_claude_conversation_render.py`'s `render_conversation`,
> extracted from `main()` specifically so tests could exercise it
> directly) — but orchestrators like `path_render.py` still invoke
> these as subprocesses (`subprocess.run([render_script, chat_dir],
> stdout=out_file)`) rather than importing and calling the function
> in-process. Converting that boundary too is a further move, tracked
> under the shared-code-among-providers boundary-refinement question,
> not required to close this decision.
