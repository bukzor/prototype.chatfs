---
why:
  - stack-split
  - provider-agnostic-interface
---

# Package Division

One package per subsystem, named for its role; directory under `packages/`
equals the distribution/crate name. (Interim rule — defers to the polyglot
dir-naming sweep, `.claude/todo.kb/2026-05-16-001-polyglot-package-dir-naming-sweep.md`,
if it decides otherwise.)

## Python (uv workspace)

- **`chatfs-cli`** — the pipeline: capture orchestration, pluck, splat,
  render, cache layout. Import package is **`chatfs`** (distribution and
  import names decouple; the bare import keeps module paths readable:
  `chatfs.provider.chatgpt.conversation…`). Providers nest under
  `chatfs.provider`, not separate distributions — the adapter seam is
  small and freshly stabilized, and per-provider code carries no
  divergent dependencies.
- **`bukzor.chatgpt-export`** — prior art, unchanged.

> [!TODO]
> `chatfs-cli` is today's `chatfs` distribution, renamed; the pipeline
> lands there from `docs/dev/design-incubators/chatfs-cli-mockup/`.
> Tracked: `.claude/todo.kb/2026-07-13-000-graduation-and-integration.kb/`.

## Rust (cargo workspace)

- **`chatfs`** — bin crate: the `chatfs` binary. `chatfs mount` (FUSE
  daemon: serving, control plane, in-daemon job queue); later home of the
  git-style dispatcher (`070-future-work.kb/cli-subcommand-dispatcher.md`),
  which is language-agnostic exec and so doesn't care that the kebab
  commands it dispatches to are Python.
- **`chatfs-fuser`** — lib crate: generic declarative FUSE builder. Not
  chatfs-specific; carries no chatfs policy.

> [!TODO]
> The `chatfs` bin crate does not exist yet. Ordering constraint: the
> Python rename above frees the `packages/chatfs` directory first.

## Node (pnpm workspace)

- **`har-browse`** — browser-driven HAR capture. Deliberately
  chatfs-agnostic (see `../../technical-policy.kb/`'s opaque-extractor
  boundary) and therefore generically named.

## Extension-point naming (preemptive; use only when/if needed)

- **Python providers** split out or third-party: distribution
  `chatfs-provider-<name>`, discovered via entry-point group
  `chatfs.providers`. Trigger to split: a provider grows heavy
  dependencies, or an external party ships one.
- **Rust components** split out of the daemon: `chatfs-<component>`,
  split only on proven reuse.
- **Node**: chatfs-specific packages (none expected) take `chatfs-*`;
  generic browser tooling stays generically named.

**Why not per-provider packages now.** The provider/universal boundary
collapsed to a small fixed adapter (see the incubator's
`provider-plugin-model.md`); entry-point discovery provides the extension
mechanism without distribution overhead, and splitting later is cheap.
