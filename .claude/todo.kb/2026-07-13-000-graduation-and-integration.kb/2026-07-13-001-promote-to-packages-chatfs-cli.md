---
managed-by: Skill(llm-subtask)
blocked-by:
  - 2026-07-13-000-module-shape-refactor.md
related-effort: docs/dev/design.kb/040-design.kb/package-division.md
cost-benefit-sweh:
  timebox:
    "@value": 4.0
    rationale: >
      git mv + packaging metadata + reference sweep. The 2026-07-10
      incubator rename was the same shape and closed in-session; entry
      points and todo re-homing add some breadth.
    confidence: tentative
  benefit-2w:
    "@value": 1.0
    rationale: >
      Pipeline installable and runnable from $PATH; frees the
      packages/chatfs directory name for the Rust bin crate.
    confidence: tentative
---

# Promote pipeline to `packages/chatfs-cli/`

**Priority:** High
**Complexity:** Medium (mechanical but wide)
**Context:** Package names/conventions:
`docs/dev/design.kb/040-design.kb/package-division.md`. Entry-point naming:
incubator `design.kb/040-design.kb/cli-command-shape.md` (`chatfs
chatgpt conversation url browse` → `chatfs-chatgpt-conversation-url-browse`
on `$PATH`).

## Problem Statement

The packaged `chatfs` python distribution is a stub with superseded
`layer/` scaffolding; the real pipeline lives in the incubator. Rename the
distribution to `chatfs-cli`, move the (now package-shaped) pipeline in,
and expose the CLI surface as installed entry points.

## Implementation Steps

- [ ] Rename: `packages/chatfs/` → `packages/chatfs-cli/`, distribution
      `chatfs` → `chatfs-cli` (import package stays `chatfs`); update uv
      workspace refs (root `pyproject.toml` dependency + sources).
- [ ] `git mv` the incubator's `chatfs/` package into
      `packages/chatfs-cli/lib/chatfs/` (tests ride along); delete the
      legacy `layer/` scaffolding and its READMEs.
- [ ] `[project.scripts]`: one `chatfs-<provider>-<noun>-<verb>` entry per
      orchestrator/leaf; decide fate of the stub `chatfs = chatfs.cli:main`
      script (likely: drop — the `chatfs` command name belongs to the
      future Rust binary).
- [ ] Drop the root `pyproject.toml` pyright `executionEnvironments`
      workaround (its comment names this graduation as the removal
      trigger).
- [ ] Re-home unclosed incubator todos (`.claude/todo.md` + `todo.kb/`)
      to `packages/chatfs-cli/.claude/`, updating relative links; carried,
      not drained (user call 2026-07-13).
- [ ] Incubator README → historical: what it settled, where the code
      went; `chatfs.demo/` tree and captured fixtures stay put unless a
      test needs them relocated.
- [ ] Reference sweep (2026-07-10 rename precedent): grep repo-wide for
      old paths; fix living docs, leave devlogs.

## Open Questions

- Do the demo captures / test fixtures move with the tests that read
  them, or stay incubator-local with tests pointing in? Decide when the
  first moved test breaks.

## Success Criteria

- [ ] `uv sync` from repo root installs `chatfs-cli`; entry points run
      from any cwd against an explicit cache-root argument.
- [ ] Full test suite + basedpyright clean from repo root, no
      per-incubator pyright scoping.
- [ ] `packages/chatfs` directory name is free.
