---
managed-by: Skill(llm-subtask)
blocked-by:
  - 2026-07-13-002-path-ownership-contract-v1.md
related-effort: ~/.claude/skills/llm-kb/.claude/todo.kb/2026-07-13-000-cross-kb-cooperation-conventions.md
cost-benefit-sweh:
  timebox:
    "@value": 4.0
    rationale: >
      Three bounded docs tasks: one rewrite (stack-split), one curated
      entry migration under interim cross-kb conventions, one ADR.
      Overrun means the cross-kb conventions question is leaking in —
      stop and let the upstream subtask handle it.
    confidence: tentative
  benefit-2w:
    "@value": 1.0
    rationale: >
      Removes the known-misleading design doc (stack-split's stale
      ownership lists) before daemon work builds on it; closes the
      incubator's fold-lessons-back contract.
    confidence: tentative
---

# design.kb reconciliation + graduation ADR

**Priority:** Medium
**Complexity:** Low-Medium
**Context:** Two drivers. (1) `docs/dev/design.kb/040-design.kb/stack-split.md`
is stale: it assigns cache layout, markdown generation, orchestration, and
the provider registry to Rust; ground truth is a three-way split (Python
chatfs-cli owns the pipeline; Rust owns FUSE serving + job queue; Node owns
the browser). Diagnosed 2026-07-13: it drifted *because* a project-level
doc asserted subsystem internals. (2) The incubator README's contract:
"Lessons settled here get folded back to project-level design.kb" — the
code graduation (sibling child 001) has this documentation twin.

## Implementation Steps

- [ ] Rewrite `stack-split.md` seams-only: the three-way split, invocation
      direction (Rust → Python CLI → Node sidecar, subprocess + files),
      pointing at the path-ownership contract and `package-division.md`;
      no subsystem-internal ownership enumerations. Keep the language-
      choice rationale ("why not all-Rust", "why not long-lived sidecar").
- [ ] Graduate incubator design entries under **interim cross-kb
      conventions** (symlinks for shared files, relative cross-kb
      references, backlink grep on moves): package-internal decisions
      (`cli-command-shape` + sub-kb, `driver-model`,
      `stdio-pipeline-shape`, incubator `provider-plugin-model` lessons)
      → `packages/chatfs-cli` scope; cross-subsystem decisions
      (`chat-as-directory` + sub-kb, `deterministic-regeneration`,
      `no-partial-synthesis`, `browse-incidental-capture`) → evaluate
      one-by-one for project 040 vs package scope. Curated, not bulk —
      the naive-push failure mode is the thing to avoid.
- [ ] ADR (`docs/dev/adr/`): the graduation itself — incubator closed,
      what it settled, where code and docs went.
- [ ] Sweep: dead links repo-wide (living docs fixed, devlogs left);
      incubator design.kb left as pointers or removed per what
      graduation leaves behind.

## Open Questions

- Per-entry placement calls (package kb vs project 040) — resolve during
  the curated pass; when genuinely ambiguous, the seams-only rule
  decides (does it constrain more than one package?).

## Success Criteria

- [ ] Project 040 contains no claims about any single package's
      internals.
- [ ] Every graduated entry reachable from its new home's `ls`; no
      dangling `why:` or prose links (repo-wide grep + `find -xtype l`
      clean).
- [ ] ADR recorded; incubator README points at it.
