---
managed-by: Skill(llm-subtask)
---

# Drain too-many-changes freeze

**Priority:** High — clear before more work piles on. The freeze isn't actively blocking, but it's risk: every day it sits, the more entangled the context becomes for re-engagement. User flagged "festering" concern.
**Complexity:** Low. Most extraction is mechanical; the architectural ambiguity (Stream 2 obsolescence) has been resolved in favor of skip.
**Context:** Frozen WIP at `../prototype.chatfs.too-many-changes/` branch `too-many-changes` (merge-base `bd23dd1`, snapshot `7ef4517`). 166 files still diverge vs `main`. See planning commits `4734e91` (BARRIER landing plan) and `d7cc41a` (depends-frontmatter encoding) in that branch.

## Provenance audit (2026-05-19)

User-confirmed decisions are folded into the plan below. Earlier drafts contained inferred specifics (wrong file paths, hallucinated test names, an architectural framing that turned out to be backwards); the conversation on 2026-05-19 resolved these.

**Authoritative sources, in order:**

1. User's direct decisions in the 2026-05-19 conversation.
2. `../prototype.chatfs.too-many-changes/` commit `7ef4517` message — 3-stream scope.
3. `../prototype.chatfs.too-many-changes/docs/dev/devlog/2026-05-12-001-har-browse-tail-latency-closure.md` — what Stream 2 actually closed.
4. `git diff main..too-many-changes` from the freeze worktree — current divergence.

**User-resolved decisions:**

- Stream 2 stress tests: **drop all of them**. User recall: most freeze stress tests are abortive side-experiments; the two that paid out are subsumed by BARRIER (already on main). BARRIER is strictly stronger than the `/done`-mechanism tests it replaced.
- Stream 2 paper trail: **conservative**. Land only what's relevant to future agents/humans working in this repo; user suspects most doesn't meet that bar.
- Stream 1 infra (refactor + jq fix + recursive mismatch + trash.sh): **land as one commit**.
- Stream 1 learnings: **promote to project-level** (not in-place in incubator). Two to `docs/dev/learnings.kb/`, two to `docs/dev/technical-policy.kb/`.
- Worktree end state: **rename branch with `archive/` prefix; remove worktree**.
- Phase 1 reread before extraction: **yes**.

## Plan

### Phase 1 — Reread (short; confirm-or-refute, not deep dive)

- [ ] Spot-check BARRIER 002/003/004 → main commit mapping (`35fec81`, `7169dea`+`0de80cd`, `ff1e8a0`). Verified for 001; the rest are inferred from commit-message wording. One read each is enough.
- [ ] Open `docs/dev/devlog/2026-05-12-001-har-browse-tail-latency-closure.md` end-to-end. Decide which parts of the closure narrative (if any) are useful for future agents/humans working in this repo. Default: skip.
- [ ] Skim `packages/har-browse/.claude/todo.kb/2026-05-12-000-tail-latency-buffering-investigation.md` (+693 lines). Almost certainly drop — it's an investigation log of a closed investigation, and BARRIER subsumes its conclusion. Confirm before discarding.
- [ ] Decide whether any of the 3 dev.kb discoveries (`fifo-completeness-guarantee.md`, `cdp-capture-loss-decomposition.md`, `network-completeness-drain-mechanism.md`) describe a still-load-bearing fact a future agent needs. Default: skip; BARRIER's design comments are the canonical record now.

### Phase 2 — Extract Stream 1

- [ ] **Commit 1: chatfs-mockup-chatgpt incubator infra**
    - [ ] `chatfs_claude_layout.py`: add `capture()` helper (+36)
    - [ ] `chatfs_claude_conversation_url_browse.py`: refactor to use `capture()`; make `null_tolerant_mismatches` recursive (±75)
    - [ ] `chatfs_claude_conversation_path_browse.py`: refactor to use `capture()` (−20)
    - [ ] Four `*_pluck.jq` files: add `| strings  # 204, interrupted responses` before `fromjson` (±4 each)
    - [ ] New `chatfs_claude_conversation_url_trash.sh` (+32)
    - [ ] `.claude/todo.md` tweak in the incubator (±4)
- [ ] **Commit 2: promote learnings to project-level**
    - [ ] `commits-bounded-by-test-assertion-change.md` → `docs/dev/learnings.kb/`
    - [ ] `linter-warnings-name-work-to-do.md` → `docs/dev/learnings.kb/`
    - [ ] `robustness-target-wire-format-permitted.md` → `docs/dev/technical-policy.kb/`
    - [ ] `zero-data-loss-is-the-correctness-target.md` → `docs/dev/technical-policy.kb/`
    - [ ] Strip any incubator-specific phrasing; verify each reads as project-level guidance
    - [ ] Add any needed cross-references from existing technical-policy.kb entries

### Phase 3 — Extract Stream 2 paper trail (conservative)

Default posture: skip. Only land items that survive the Phase-1 "useful to future agents/humans" filter.

- [ ] Closure devlog `docs/dev/devlog/2026-05-12-001-har-browse-tail-latency-closure.md` — likely yes; the BARRIER pivot narrative is genuinely useful context for anyone touching `capture.mjs` next.
- [ ] Learnings `runtime-bindingcalled-fifo-with-network-rwb.md` — assess in Phase 1; likely yes if it's specific FIFO discovery, no if it's redundant with the closure devlog.
- [ ] Diff to `2026-04-24-001-har-browse-cdp-may-trail-visual-interactability.md` (±29) — small status-update diff; probably yes if it's marking a claim as resolved.
- [ ] 3 dev.kb discoveries — probably no per Phase 1 default.
- [ ] +693-line investigation log — probably no per Phase 1 default.

### Phase 4 — Archive freeze

- [ ] `git -C ../prototype.chatfs.too-many-changes/ branch -m too-many-changes archive/too-many-changes`
- [ ] `git worktree remove ../prototype.chatfs.too-many-changes/`
- [ ] Verify `git branch -a` on main repo shows `archive/too-many-changes` (so the WIP and planning commits remain findable in `git log` for any future need)

## Acceptance

- [ ] BARRIER 001-004 → commit mapping verified for all four
- [ ] Commit 1 landed: incubator infra (refactor + jq fix + recursive mismatch + trash.sh)
- [ ] Commit 2 landed: 4 learnings promoted to `docs/dev/{learnings.kb,technical-policy.kb}/`
- [ ] Phase 3 decisions made and acted on (whatever the conservative landing turns out to be — could be zero commits, could be the closure devlog only)
- [ ] Branch renamed to `archive/too-many-changes`; worktree removed
- [ ] No remaining diff in working tree of main repo from this drain effort

## Notes

- The pending `2026-05-11-000-rename-incubator-to-chatfs-cli-mockup` does *not* block this work — incubator rename is a future `git mv`; landing Stream 1 in the current name is fine.
- The 9 `stress-event-storm-*` experimental variants (and the rest of the freeze tests dir) die with the worktree but live on in the `archive/too-many-changes` branch — recoverable if ever needed via `git checkout archive/too-many-changes -- packages/har-browse/tests/`.
- The 4 BARRIER task files in the freeze are useful for understanding the commit decomposition retrospectively, but the landed commits on `main` already implement them — those task files do not themselves need to land.
- Drafting hygiene reminder: read the actual planning artifacts before writing breakdowns of them. The first draft of this file invented specifics (wrong file paths, hallucinated test names) from `git diff --stat` alone. Verify against the freeze, not against pattern-matching on commit titles.
