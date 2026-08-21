--- # workaround: anthropics/claude-code#13003
depends:
  - Skill(llm-design-kb)
---

# chatfs-cli — Design Knowledge

Package-scoped design decisions: how the capture/splat/render pipeline
behaves in ways future sessions must honor. Mission, goals, requirements,
and cross-package seams live in the project tower, `docs/dev/design.kb/`;
entries here link upward via `why:` paths reaching into that tower.
Graduated 2026-08-08 from the chatfs-cli-mockup incubator with the code
(see `docs/dev/adr/` graduation entry).

## Collections

- `040-design.kb/` — Decisions about pipeline shape, CLI surface,
  regeneration semantics, and the contract between browse and downstream
  stages.
