--- # workaround: anthropics/claude-code#13003
depends:
  - Skill(llm-kb)
---

# FUSE VFS — Incubator

Cleanroom subproject: learn FUSE filesystem mechanics using fuser, building
toward the chatfs mount layer. Produces a reusable VFS crate for serving cached
content as a filesystem.

## Source Material

Design principles extracted from a ChatGPT design session (2026-03-04). See:
- `data/todo-llmfs.chatgpt.com.splat/extracted/02-design-spec-9-section.md`
- `data/todo-llmfs.chatgpt.com.splat/extracted/03-architectural-invariants.md`

## Collections

- `010-mission.kb/` — What this subproject exists to accomplish
- `020-goals.kb/` — Aspirational outcomes that guide requirements
- `030-requirements.kb/` — Verifiable acceptance criteria
- `040-design.kb/` — Architecture and major abstractions
- `050-components.kb/` — Subsystems and their responsibilities
- `060-deliverables.kb/` — Milestones and build artifacts
