<anthropic-skill-ownership llm-subtask />

# Tactical Tasks

Driver: [Harmonize with llm-* skills](todo.kb/2026-01-02-000-harmonize-with-llm-skills.md) — most done; chatfs-local remaining items below.

## chatfs-mockup-chatgpt — next sessions

Plan from 2026-05-05 design.kb consolidation. Order is dependency-driven; 1-2 are blocking, 3-4 are deferrable. Incubator-tactical breakdowns at `docs/dev/design-incubators/chatfs-mockup-chatgpt/.claude/todo.kb/`.

1. [ ] **`.chat/$UUID/` implementation.** Land storage-vs-view in code: `place_meta` writes to `.chat/$UUID/`, view-symlink purge, captured/derived allowlist in `path_render`. Design persisted at `docs/dev/design-incubators/chatfs-mockup-chatgpt/design.kb/040-design.kb/chat-as-directory.md`. Smoke test: byte-for-byte reproduction against the existing 134-turn chat.
2. [ ] **README rewrite + end-to-end test.** Depends on (1). Update README pipeline diagram + `Run it` block to tested paths; run live `har-browse` (interactive, needs human at keyboard). Folds in: fate of `chatfs_chatgpt_conversation_url_render.py` — keep, fold into `path_render`, or delete.
3. [ ] **Noun-verb sub-kb** (deferrable). Per-cell scope. Trigger when actually adding a new verb/noun, not speculatively. Plan at `docs/dev/design-incubators/chatfs-mockup-chatgpt/.claude/todo.kb/2026-05-05-002-plan-and-create-noun-verb-model-sub-kb.md`.
4. [ ] **Multi-provider sketch** (deferrable). `chatfs.demo/claude/` parallel to `chatgpt/`; tests the parent project's `provider-plugin-model.md` against a second provider in practice. Also the natural moment to promote the incubator's `provider-plugin-model.md` symlink to a real entry or sub-kb.

## Deferred

- [ ] Create `docs/dev/milestones.kb/` — double-blocked (no milestone content yet; skills-repo pattern not defined)

## Upstream (mirrors of skills-repo todos; kept here for visibility)

- [ ] llm-kb: complete `.d → .kb` rename in `complete-example/` — tracked at `~/.claude/skills/llm-kb/.claude/todo.kb/2026-01-02-000-complete-d-to-kb-rename.md`
- [ ] llm-collab: define `milestones.kb/` pattern in skeleton — tracked at `~/.claude/skills/llm-collab/.claude/todo.kb/2025-12-11-000-update-skeleton-to-match-docsdev-pattern-from-git-partial.md`
