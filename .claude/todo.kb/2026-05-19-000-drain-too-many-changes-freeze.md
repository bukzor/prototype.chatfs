---
managed-by: Skill(llm-subtask)
status: done
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

- [x] Spot-check BARRIER 002/003/004 → main commit mapping (`35fec81`, `7169dea`+`0de80cd`, `ff1e8a0`). All four match commit-message wording exactly.
- [x] Open `docs/dev/devlog/2026-05-12-001-har-browse-tail-latency-closure.md` end-to-end. **Land.** Coherent narrative of the BARRIER pivot; cites real file:line evidence; valuable future-agent context.
- [x] Skim `packages/har-browse/.claude/todo.kb/2026-05-12-000-tail-latency-buffering-investigation.md` (+693 lines). **Drop.** Investigation log; closure devlog captures the conclusion.
- [x] Decide whether any of the 3 "dev.kb discoveries" describe a still-load-bearing fact. **Plan was wrong about these.** They're not dev observations — they're 3 design.kb docs under `packages/har-browse/design.kb/{030-requirements,040-design}.kb/`: the FIFO completeness *requirement spec*, the three-source capture-loss *taxonomy*, and the drain-mechanism *design rationale*. Main has 3-line BARRIER code comments only; the requirement spec exists nowhere else. **Land all 3**, plus the `runtime-bindingcalled-fifo-with-network-rwb.md` claim they reference, with light edit to strip refs to dropped `stress-event-storm-{fifo,binding-only,counter-drain}/` tests.

### Phase 2 — Extract Stream 1

- [x] **Commit 1: chatfs-mockup-chatgpt incubator infra** — `8dc4c08`
    - [x] `chatfs_claude_layout.py`: add `capture()` helper (+36)
    - [x] `chatfs_claude_conversation_url_browse.py`: refactor to use `capture()`; make `null_tolerant_mismatches` recursive (±75)
    - [x] `chatfs_claude_conversation_path_browse.py`: refactor to use `capture()` (−20)
    - [x] Four `*_pluck.jq` files: add `| strings  # 204, interrupted responses` before `fromjson` (±4 each)
    - [x] New `chatfs_claude_conversation_url_trash.sh` (+32)
    - [~] `.claude/todo.md` tweak in the incubator (±4) — **skipped**; the freeze's version is a pre-migration `<anthropic-skill-ownership/>` marker that main already migrated to `managed-by:` frontmatter (`cd2ed85`). Taking the freeze's version would un-migrate.
- [x] **Commit 2: promote learnings to project-level** — `00ec42d`
    - [x] `commits-bounded-by-test-assertion-change.md` → `docs/dev/learnings.kb/`
    - [x] `linter-warnings-name-work-to-do.md` → `docs/dev/learnings.kb/`
    - [x] `robustness-target-wire-format-permitted.md` → `docs/dev/technical-policy.kb/`
    - [x] `zero-data-loss-is-the-correctness-target.md` → `docs/dev/technical-policy.kb/`
    - [x] Strip any incubator-specific phrasing — only `robustness-target-wire-format-permitted.md` needed it (the "Promotion target" subsection, removed); other three read as project-level already.
    - [~] Cross-references — none added. Existing technical-policy.kb entries (`architectural-invariants.md`, `atomic-cache-updates.md`, `no-work-on-read.md`, `opaque-extractor-boundary.md`, `policy-safe-automation-boundary.md`) don't have obvious load-bearing links to either new entry. Left for the user to add when context warrants.

### Phase 3 — Extract Stream 2 paper trail (revised again after deeper Phase-1 read)

**Decision: skip everything.** A closer read of `packages/har-browse/src/capture.mjs` on main against the freeze's design.kb docs shows the freeze's documents describe a forward-looking design that did not land:

- Main's Done detection still uses the DOM poll `document.getElementById("capture-done")?.dataset.clicked` (`capture.mjs:138`).
- Main's `harBrowseMark` binding only dispatches on `BARRIER:` payload prefix; the `DONE` / `DRAIN_NETWORK` / `harBrowseMark()` no-arg variants the docs describe do not exist on main.
- The fifo-completeness requirement specifies "before DONE marker"; main has no DONE marker.

What actually landed from the 2026-05-12 session: BARRIER snapshot-defer on `BARRIER:` prefix, payload `n` counter, causal-watermark, reentrant BARRIER. The DOM-poll → binding-marker pivot and the drain-handshake described in the closure devlog and design.kb never shipped.

Landing these docs as-is would document an API that doesn't exist on main; editing them to match main would be substantial rewrites better done fresh. Per the conservative posture, skip all five candidates. They remain recoverable from `archive/too-many-changes` if a future BARRIER follow-up wants to pick up where the freeze left off.

**Skipped**:
- Closure devlog `docs/dev/devlog/2026-05-12-001-har-browse-tail-latency-closure.md` — interleaves landed (`awaitingBody` rename, BARRIER) and unlanded (DONE marker, drain handshake) work; would mislead.
- `packages/har-browse/design.kb/030-requirements.kb/fifo-completeness-guarantee.md` — requirement specifying a marker that doesn't exist.
- `packages/har-browse/design.kb/040-design.kb/cdp-capture-loss-decomposition.md` — taxonomy is universal, but oracle references dropped tests.
- `packages/har-browse/design.kb/040-design.kb/network-completeness-drain-mechanism.md` — describes a drain handshake not on main.
- `docs/dev/design-incubators/chatfs-mockup-chatgpt/dev.kb/claims.kb/runtime-bindingcalled-fifo-with-network-rwb.md` — claim is universally true, but its `evidence:` frontmatter cites three dropped tests.
- Diff to `2026-04-24-001-har-browse-cdp-may-trail-visual-interactability.md` (±29) — user said don't touch without their go-ahead.
- +693-line investigation log — investigation record; closure devlog (also skipped) was the summary.

### Phase 4 — Archive freeze

- [x] `git branch -m too-many-changes archive/too-many-changes` (from main repo; cross-worktree rename works because all worktrees share `.git/`)
- [x] `git worktree remove --force ../prototype.chatfs.too-many-changes/` — `--force` because the worktree had uncommitted edits (3 reverts of the ownership-marker migration + 2 in-progress edits on `2026-05-12-002`/`-003` BARRIER task files; per plan, all discardable).
- [x] Verify `git branch -a` shows `archive/too-many-changes` at `07c284f`, 4 commits ahead of merge-base `bd23dd1`.

## Acceptance

- [x] BARRIER 001-004 → commit mapping verified for all four (`a7912c3`, `35fec81`, `7169dea`+`0de80cd`, `ff1e8a0`)
- [x] Commit 1 landed: incubator infra (refactor + jq fix + recursive mismatch + trash.sh) — `8dc4c08`
- [x] Commit 2 landed: 4 learnings promoted to `docs/dev/{learnings.kb,technical-policy.kb}/` — `00ec42d`
- [x] Phase 3 decisions made and acted on — closer read of `capture.mjs` on main revealed the freeze's design.kb describes the DOM-poll → binding-marker pivot that didn't ship; skipped all 5 Stream-2 candidates rather than land docs documenting an unlanded API.
- [x] Branch renamed to `archive/too-many-changes`; worktree removed.
- [x] No remaining diff in working tree of main repo from this drain effort (only this kb file itself, which lands as the closeout record).

## Closeout

Two commits landed on `main` from the drain:
- `8dc4c08 chatfs-mockup-chatgpt: capture() helper, recursive null-tolerant cross-check, jq tolerance for bodyless responses`
- `00ec42d docs/dev: promote 4 learnings from chatfs-mockup-chatgpt to project scope`

Material plan revisions made during execution (both auditable above): (a) the "3 dev.kb discoveries" were actually 3 design.kb docs; reconsidered as worth landing; then (b) a closer read against `capture.mjs` on main revealed they describe an unlanded forward design, so reverted to "skip all Stream-2 paper trail" per the user's conservative posture.

Residual state worth flagging to the user:

- Removed two abandoned side-worktrees at user instruction: `../prototype.chatfs.chatfs-mockup-residuals/` and `../prototype.chatfs.tail-latency-closure/`, both checked out at `bd23dd1` (older than main) with 3 modified `.claude/todo.kb/*` files each (all reverts of the `cd2ed85` ownership-marker migration; no useful work to preserve). Branch names suggest they were originally staged as separate landing branches for Streams 1 and 2 of this drain; the drain landed directly on main instead. The branches themselves (`chatfs-mockup-residuals`, `tail-latency-closure`) still exist as labels pointing at `bd23dd1` — they preserve nothing unique (bd23dd1 is in main's history) and can be pruned with `git branch -D` whenever desired.
- Pending project-level todos remain in `.claude/todo.kb/` (incubator rename, rust-port-kb home, polyglot package naming sweep, rust-port-kb scope refactor). None blocked on this drain.
- `archive/too-many-changes` branch retains the freeze's 4 commits + the closure devlog, design.kb docs, claim, BARRIER task files, and stress tests. Recoverable via `git checkout archive/too-many-changes -- <path>` if any future BARRIER follow-up wants to pick up where the freeze left off.

## Notes

- The pending `2026-05-11-000-rename-incubator-to-chatfs-cli-mockup` does *not* block this work — incubator rename is a future `git mv`; landing Stream 1 in the current name is fine.
- The 9 `stress-event-storm-*` experimental variants (and the rest of the freeze tests dir) die with the worktree but live on in the `archive/too-many-changes` branch — recoverable if ever needed via `git checkout archive/too-many-changes -- packages/har-browse/tests/`.
- The 4 BARRIER task files in the freeze are useful for understanding the commit decomposition retrospectively, but the landed commits on `main` already implement them — those task files do not themselves need to land.
- Drafting hygiene reminder: read the actual planning artifacts before writing breakdowns of them. The first draft of this file invented specifics (wrong file paths, hallucinated test names) from `git diff --stat` alone. Verify against the freeze, not against pattern-matching on commit titles.
