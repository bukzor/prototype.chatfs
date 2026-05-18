---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 1.0
    rationale: |
      File-level estimate for a 6-item rollup that's mostly tracking
      upstream skill work. Only the mockup-chatgpt rename is actual
      tactical work here.
  benefit-2w:
    "@value": 0.5
    rationale: |
      Most payoff is double-counted in upstream items (llm-kb/todo.md,
      rust-port kb scope refactor). Local payoff is the mockup-chatgpt
      rename plus better visibility into cross-repo blockers.
---

# Tactical Tasks

Driver: [Harmonize with llm-* skills](todo.kb/2026-01-02-000-harmonize-with-llm-skills.md) — most done; chatfs-local remaining items below.

## chatfs-mockup-chatgpt — next sessions

Plan from 2026-05-05 design.kb consolidation. Order is dependency-driven; 1-2 are blocking, 3-4 are deferrable. Incubator-tactical breakdowns at `docs/dev/design-incubators/chatfs-mockup-chatgpt/.claude/todo.kb/`.

1. [x] **`.chat/$UUID/` implementation.** Landed 2026-05-08; see devlog `2026-05-08-000-chatfs-mockup-chatgpt-chat-as-directory-implementation.md`.
2. [x] **README rewrite + end-to-end test.** Landed 2026-05-08; live URL test passed (188 messages / 129 turns initial, 262 / 206 follow-up). See devlogs `2026-04-29-000` and `2026-05-08-001`.
3. [x] **Noun-verb sub-kb.** Landed 2026-05-11 at `docs/dev/design-incubators/chatfs-mockup-chatgpt/design.kb/040-design.kb/cli-command-shape.kb/` (partition-prefix scope, Hive-style `key=value` naming). See devlog `2026-05-11-000-chatfs-mockup-chatgpt-cli-command-shape-kb.md`.
4. [ ] [Rename incubator to chatfs-cli-mockup](todo.kb/2026-05-11-000-rename-incubator-to-chatfs-cli-mockup.md) — precursor to multi-provider sketch; current name encodes a single provider.
5. [ ] **Multi-provider sketch** (deferrable). Scope B from 2026-05-11 conversation: hand-prepare a Claude data-export-derived `chatfs.demo/claude/.chat/$UUID/` and run splat + render through it; no live BB1 capture from claude.ai yet. Tests the parent project's `provider-plugin-model.md` against a second provider in practice. Also the natural moment to promote the incubator's `provider-plugin-model.md` symlink to a real entry or sub-kb.

## Rust port — kb scope refactor

- [x] [Place the rust-port kb at a proper home](todo.kb/2026-05-13-000-place-rust-port-kb-at-proper-home.md) — decided 2026-05-15; audit at `packages/har-browse/dev.kb/rust-port.kb/scope-audit.md`; session record at `~/.claude/sessions.kb/rust-port-kb-scope-refactor.md`
- [ ] [Execute the rust-port kb scope refactor](todo.kb/2026-05-16-000-execute-rust-port-kb-scope-refactor.md) — 9 steps; must land before commits 0750/1000/1050
- [ ] [Polyglot package dir naming — sweep existing packages](todo.kb/2026-05-16-001-polyglot-package-dir-naming-sweep.md) — depends on execute-rust-port above

## Deferred

- [ ] Create `docs/dev/milestones.kb/` — double-blocked (no milestone content yet; skills-repo pattern not defined)
- [ ] Write ADR for `.claude/focus.md` as symlink-to-active-artifact convention (target type = `todo.kb/<entry>.md` for plan phases, `commits.kb/<NNNN>-slug.md` for commit phases; gitignored; per-user). Adopted ad-hoc 2026-05-16 at workspace level; codify before applying to har-browse and other packages.

## Upstream (mirrors of skills-repo todos; kept here for visibility)

- [ ] llm-kb: complete `.d → .kb` rename in `complete-example/` — tracked at `~/.claude/skills/llm-kb/.claude/todo.kb/2026-01-02-000-complete-d-to-kb-rename.md`
- [ ] llm-collab: define `milestones.kb/` pattern in skeleton — tracked at `~/.claude/skills/llm-collab/.claude/todo.kb/2025-12-11-000-update-skeleton-to-match-docsdev-pattern-from-git-partial.md`
