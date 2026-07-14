# Devlog: 2026-07-13 — graduation and integration planning

## Focus

Planning-only session: lay out the arc from the chatfs-cli-mockup
incubator (three providers feature-complete) through packaging to a
working `chatfs mount`. Deliverables are documentation: a strategic
umbrella with six children (`.claude/todo.kb/2026-07-13-000-graduation-and-integration.md`
+ `.kb/`), two design entries, one first-priority incubator todo, one
upstream skills-repo item, and this entry.

## Decisions

### Package division (three ecosystems, one package per subsystem)

Python dist `chatfs-cli` (import package stays `chatfs`); Rust bin crate
`chatfs` (the binary: `mount`, later the dispatcher) beside lib crate
`chatfs-fuser`; Node `har-browse` unchanged. Extension-point conventions
declared preemptively (`chatfs-provider-<name>` + entry-point group
`chatfs.providers`; `chatfs-<component>` crates), exercised only when
needed. Full statement: `design.kb/040-design.kb/package-division.md`.

**Rationale:** name-per-role; the bare `chatfs` name goes to the binary
users touch. **Alternatives considered:** `chatfs-vfs` for the Rust side
(rejected: the VFS is `chatfs-fuser`; the new crate is daemon + umbrella);
per-provider Python packages now (rejected: adapter seam freshly
stabilized, no divergent deps; entry-point discovery gives extensibility
without distribution overhead); import name `chatfs_cli` (rejected for
module-path readability; reopen on demonstrated confusion).

### Control plane is in-integration scope, not a milestone

fuser-vfs's M3 stays unscheduled as a milestone; its content (control
files, job queue, `waiting_user`) is resolved as-needed inside the
integration child. **Rationale:** M1/M2 retired the kernel-facing risks;
remaining risks (write-path POSIX semantics vs the crate's read-only-
shaped statelessness; daemon-spawns-browser session plumbing) are
integration-shaped and would be settled wrong in isolation. This reversed
the session-opening assessment ("M3 is a missing major step") — the
question is where risk gets discovered, not whether the work is listed.

### Read-only mount is a real deliverable

A mount serving the materialized tree with manual CLI sync delivers the
mission's composability (grep/ls/cat/editors) for captured data; only
laziness waits on the control plane. (Corrected from "delivers none of
the lazy-filesystem goal".)

### Job queue: bespoke in-daemon; Rayon is the wrong shape

Rayon is CPU-bound data-parallelism; sync jobs are subprocess-wait-bound
and need keyed dedup + introspectable state. Channel + worker threads +
`Mutex<HashMap<JobKey, JobState>>`. Rayon stays on the shelf for
bulk-render parallelism *inside* a job. External brokers rejected: IPC +
service dependency for a personal filesystem daemon.

### Rust↔Python seam documented as path ownership

Not command/arg enumeration (single-sourced in the owning package;
reference, don't dup): which subpaths each component wholly owns vs
reads. Standards doc in `technical-policy.kb/`, reviewable per se,
expected to evolve. Descriptive v1 is umbrella child 002.

### Seams-only rule for the project design.kb

`stack-split.md` drifted because a project-level doc asserted subsystem
internals ("Rust owns markdown generation…"). Rule: project 040 states
seams between subsystems; internals live in package-scoped kbs. The
rewrite is umbrella child 005 (kept there rather than hot-fixed here:
it depends on the contract v1 and deserves the considered pass).

### Interim-decision pattern, four items

Cross-kb conventions (symlinks + relative refs + backlink grep); path
ownership (descriptive v1); extension-point naming (declared, unused);
import name (`chatfs`). Each unblocks dependent work now while its
considered track proceeds independently.

### Scope-of-work layout: llm-subtask schedules, llm-design-kb models

Will-be-checked-off → todo.kb (sub-kb nesting for parent/child,
`blocked-by` for edges); true-indefinitely → design.kb (`[!TODO]`-marked
where not yet built); happened → devlog. design.kb's why-chains are
justification, not a scheduling DAG — it is deliberately *not* up to the
scheduling job.

### Other calls

- Atomic-cache-updates promoted to first-priority incubator todo
  (requirement violated by in-place regeneration; precondition for
  serving trees from a mount). Unclosed incubator todos re-home with the
  code; carried, not drained.
- Cache root stays an argument everywhere, possibly indefinitely —
  per-mount stability is all the VFS needs; XDG defaults are deferrable
  ergonomics.
- Git-style dispatcher + autocomplete: `070-future-work.kb/cli-subcommand-dispatcher.md`,
  punt indefinitely.
- Cross-kb cooperation conventions: upstream llm-kb item (primary at
  `~/.claude/skills/llm-kb/.claude/todo.kb/2026-07-13-000-cross-kb-cooperation-conventions.md`,
  mirrored in root todo.md Upstream), hypothesis: generic llm-kb
  mechanics suffice, llm-design-kb adds a thin layer-crossing policy.
- On hold untouched: claude-code provider, har-browse Rust port,
  reasoning-slot gap, fork-representation (read-side settled by
  rotate-90).

## Conventions Established

- Dependency edges between strategic tasks: `blocked-by:` frontmatter on
  the blocked child; parent/child via `<stem>.kb/` nesting; conceptual vs
  representational nature of each edge noted in prose (the 001→003 edge
  is name-availability only — relaxable for parallelism).
- Design decisions made during planning are written to design.kb
  immediately with `[!TODO]` markers; todo children reference them
  rather than restating.

## Open Questions

- Module layout details (nouns as subpackages vs modules; jq filters;
  `.sh` conversion) — deferred to child 000's layout-writing step.
- Per-entry placement calls in the design.kb graduation — child 005's
  curated pass; seams-only rule decides ambiguity.

## References

- `.claude/todo.kb/2026-07-13-000-graduation-and-integration.md` — the plan
- `docs/dev/design.kb/040-design.kb/package-division.md` — names/conventions
- `docs/dev/design-incubators/chatfs-cli-mockup/.claude/todo.kb/2026-07-13-000-Atomic-chat-dir-regeneration---stage-and-rename--never-rewrite-in-place.md`
- `docs/dev/design.kb/040-design.kb/{sync-control-plane,work-enqueueing-model,black-box-decomposition,stack-split}.md` — the designs integrated against
- fuser-vfs deliverables (`docs/dev/design-incubators/fuser-vfs/design.kb/060-deliverables.kb/`) — M1/M2 solid, M3 content absorbed into umbrella child 004
