---
why:
  - black-box-decomposition.md
background:
  - fuse-filesystem
source:
  - conversations.cleaned/02-architecture-convergence/094.assistant.text.md
---

# Stack Split: Rust Mount, Python Pipeline, Node Browser

Three language runtimes, each owning what it's best at, joined only by
subprocess invocation and files on disk — never linked code:

**Rust (`chatfs-fuser` and future workspace crates) owns:** the FUSE
filesystem — serving the cache as a mount — and, when the control plane
lands, the daemon side: job queue, sync triggers, status surfaces.

**Python (`packages/chatfs-cli`) owns:** the capture → extract → render
pipeline (BB1 driving, BB2, BB3), writing the cache per the shared
on-disk contract (`docs/dev/technical-policy.kb/path-ownership.md`).
What it writes is what the mount serves. Pipeline-internal shape lives
in the package's own `design.kb/`.

**Node/Playwright (`packages/har-browse`) owns:** browser interaction
only. Opens Chromium, lets the page run, records the CDP stream, emits
it, exits. Single purpose: "record what the browser saw, exit."

## Seams

- **Python → Node:** chatfs-cli invokes `har-browse <url>` as a
  subprocess and captures its stdout stream. This is the only way
  browser output enters the system.

> [!TODO] Rust → Python: daemon invokes the CLI entry points
> The daemon executes `chatfs-provider-<provider>-<noun>-<verb>` commands as
> background jobs (subprocess; the path-ownership contract bounds what
> they may write); outputs land via the atomic staging convention, and
> the mount picks them up by re-reading the cache. Lands with the
> control-plane work (`sync-control-plane.md`,
> `work-enqueueing-model.md`).

**Why not all-Rust:** Playwright's best bindings are Node (and Python).
Rust ports lag in features. Embedding JS runtimes in Rust balloons
effort. The pragmatic split keeps kernel-facing code in Rust and
delegates browser expertise to Node.

**Why not a long-lived sidecar:** One-shot subprocesses at every seam —
each capture spawns a fresh process. Clean failure semantics, no
cascading failures, simpler packaging. If startup cost becomes annoying,
evolve to a persistent agent without changing the outer contract.
