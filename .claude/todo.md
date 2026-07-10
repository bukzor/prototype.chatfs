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

## chatfs-cli-mockup — next sessions

Plan from 2026-05-05 design.kb consolidation. Order is dependency-driven; 1-2 are blocking, 3-4 are deferrable. Incubator-tactical breakdowns at `docs/dev/design-incubators/chatfs-cli-mockup/.claude/todo.kb/`.

1. [x] **`.chat/$UUID/` implementation.** Landed 2026-05-08; see devlog `2026-05-08-000-chatfs-mockup-chatgpt-chat-as-directory-implementation.md`.
2. [x] **README rewrite + end-to-end test.** Landed 2026-05-08; live URL test passed (188 messages / 129 turns initial, 262 / 206 follow-up). See devlogs `2026-04-29-000` and `2026-05-08-001`.
3. [x] **Noun-verb sub-kb.** Landed 2026-05-11 at `docs/dev/design-incubators/chatfs-cli-mockup/design.kb/040-design.kb/cli-command-shape.kb/` (partition-prefix scope, Hive-style `key=value` naming). See devlog `2026-05-11-000-chatfs-mockup-chatgpt-cli-command-shape-kb.md`.
4. [x] [Rename incubator to chatfs-cli-mockup](todo.kb/2026-05-11-000-rename-incubator-to-chatfs-cli-mockup.md) — precursor to multi-provider sketch; current name encodes a single provider. Done 2026-07-10: `git mv` + full reference sweep (remaining old-name hits are historical: devlog filenames/bodies, the ADR title); README closing reframed to the `$REPO/lib/chatfs/` graduation target. Verified: basedpyright 0/0/0, pytest 19/19, no symlink targets the old path.
5. [x] **Multi-provider sketch** (deferrable). Scope B from 2026-05-11 conversation: hand-prepare a Claude data-export-derived `chatfs.demo/claude/.chat/$UUID/` and run splat + render through it; no live BB1 capture from claude.ai yet. Tests the parent project's `provider-plugin-model.md` against a second provider in practice. Also the natural moment to promote the incubator's `provider-plugin-model.md` symlink to a real entry or sub-kb. Superseded 2026-07-10: the claude provider landed via live BB1 capture (MVP closed 2026-05-11, devlog `2026-05-11-001`) — stronger than the hand-prepared export sketch — and AI Studio followed as a third provider (2026-06-20..07-03); the `provider-plugin-model.md` promotion landed 2026-07-09 (devlog `2026-07-09-000`). Nothing of this scope remains.

## Rust port — kb scope refactor

- [ ] [Execute the rust-port kb scope refactor](todo.kb/2026-05-16-000-execute-rust-port-kb-scope-refactor.md) — 9 steps; must land before commits 0750/1000/1050. Layered with 2026-05-21 meta-planning evolutions (see todo's "Additional decisions" section).
- [ ] [Polyglot package dir naming — sweep existing packages](todo.kb/2026-05-16-001-polyglot-package-dir-naming-sweep.md) — depends on execute-rust-port above
- [ ] **Update `packages/har-browse/dev.kb/rust-port.md` charter:** insert commit `0050` (blackbox `.spec.mjs` → CLI conversion + baseline capture) before `0100` scaffold; record commits `0025`/`0035` if diagnostic-events design and Node-side emission want separate commits. Source: `.claude/decision.kb/test-conversion-precedes-port-scaffold.md`.
- [ ] **Pre-port testing infrastructure** (Phases C/D/E) — tracked at `~/.claude/sessions.kb/har-browse-rust-port-pre-port-infrastructure.md`. Must precede commit `0800` (cdp-jsonl contract freeze) at minimum.

## Deferred

- [ ] Create `docs/dev/milestones.kb/` — double-blocked (no milestone content yet; skills-repo pattern not defined)
- [ ] Write ADR for `.claude/focus.md` as symlink-to-active-artifact convention (target type = `todo.kb/<entry>.md` for plan phases, `commits.kb/<NNNN>-slug.md` for commit phases; gitignored; per-user). Adopted ad-hoc 2026-05-16 at workspace level; codify before applying to har-browse and other packages.

## Upstream (mirrors of skills-repo todos; kept here for visibility)

- [ ] llm-kb: complete `.d → .kb` rename in `complete-example/` — tracked at `~/.claude/skills/llm-kb/.claude/todo.kb/2026-01-02-000-complete-d-to-kb-rename.md`
- [ ] llm-collab: define `milestones.kb/` pattern in skeleton — tracked at `~/.claude/skills/llm-collab/.claude/todo.kb/2025-12-11-000-update-skeleton-to-match-docsdev-pattern-from-git-partial.md`
- [x] llm-subtask: task-graph relations now modeled (2026-07-09), resolved per-field rather than one field per name. Hard dependency: canonical `blocked-by` field added to the llm-subtask base schema (`depends`/`depends-on` renamed to it). Parent/subtask-of: sub-kb nesting -- `2026-01-02-002` moved under `2026-01-02-000-harmonize-with-llm-skills.kb/`, `parent:` dropped. `supersedes-question-from`: chatfs-local `#base` extender in `.claude/todo.jsonschema.yaml`. Root stub no longer held back; `llm.kb-validate .claude` green (33 files).
