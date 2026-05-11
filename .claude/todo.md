<anthropic-skill-ownership llm-subtask />

# Tactical Tasks

Driver: [Harmonize with llm-* skills](todo.kb/2026-01-02-000-harmonize-with-llm-skills.md) — most done; chatfs-local remaining items below.

## chatfs-mockup-chatgpt — next sessions

Plan from 2026-05-05 design.kb consolidation. Order is dependency-driven; 1-2 are blocking, 3-4 are deferrable. Incubator-tactical breakdowns at `docs/dev/design-incubators/chatfs-mockup-chatgpt/.claude/todo.kb/`.

1. [x] **`.chat/$UUID/` implementation.** Landed 2026-05-08; see devlog `2026-05-08-000-chatfs-mockup-chatgpt-chat-as-directory-implementation.md`.
2. [x] **README rewrite + end-to-end test.** Landed 2026-05-08; live URL test passed (188 messages / 129 turns initial, 262 / 206 follow-up). See devlogs `2026-04-29-000` and `2026-05-08-001`.
3. [x] **Noun-verb sub-kb.** Landed 2026-05-11 at `docs/dev/design-incubators/chatfs-mockup-chatgpt/design.kb/040-design.kb/cli-command-shape.kb/` (partition-prefix scope, Hive-style `key=value` naming). See devlog `2026-05-11-000-chatfs-mockup-chatgpt-cli-command-shape-kb.md`.
4. [ ] **Multi-provider sketch** (deferrable). `chatfs.demo/claude/` parallel to `chatgpt/`; tests the parent project's `provider-plugin-model.md` against a second provider in practice. Also the natural moment to promote the incubator's `provider-plugin-model.md` symlink to a real entry or sub-kb.

## Deferred

- [ ] Create `docs/dev/milestones.kb/` — double-blocked (no milestone content yet; skills-repo pattern not defined)

## Upstream (mirrors of skills-repo todos; kept here for visibility)

- [ ] llm-kb: complete `.d → .kb` rename in `complete-example/` — tracked at `~/.claude/skills/llm-kb/.claude/todo.kb/2026-01-02-000-complete-d-to-kb-rename.md`
- [ ] llm-collab: define `milestones.kb/` pattern in skeleton — tracked at `~/.claude/skills/llm-collab/.claude/todo.kb/2025-12-11-000-update-skeleton-to-match-docsdev-pattern-from-git-partial.md`
