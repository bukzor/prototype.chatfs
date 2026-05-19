# 2026-05-19: drain-plan provenance audit (calibration)

## Focus

User opened the session lost about a frozen WIP at `../prototype.chatfs.too-many-changes/` — remembered "six good changes" and "subdivision planning" but not the count or progress. Reconstructed the picture, drafted a drain plan, then audited the plan's provenance after user pushback.

## What Happened

**Reconstruction.** From the freeze's `7ef4517` snapshot commit and main's log since `bd23dd1`, identified the structure: 3 streams in the snapshot, with stream 3 (BARRIER) split into 4 commits via a planning commit `4734e91` written on top of the freeze. 1+1+4 = 6 landings, matching user's "six." BARRIER 001-004 are all on main; streams 1 and 2 have residue.

**First-draft kb (todo.kb/2026-05-19-000-drain-too-many-changes-freeze.md) was written from `git diff --stat` alone**, without reading the actual planning artifacts. It contained: a wrong file path for the closure devlog (`dev.kb/closed.kb/...` — that dir doesn't exist), a hallucinated test name (`stress-pending-drain-loop`) in the "tests to land" list, a missed control-case test (`stress-event-storm-binding-only`), and a backwards architectural framing where Stream 2 was described as "needs to land" when in fact BARRIER is its redesign and likely subsumes it.

**User pushed back on attribution.** Spot-checked four claims against ground truth (codebase + user memory). The two claims sourced from data (git commit messages, user's words) held up; the three claims I generated (specific stress-test list, closure file path, Stream-2-needs-completion framing) all broke. Confirmed the pattern user named: I tend to present my own inferences as confident facts and flag user-or-git-sourced specifics as "open questions worth asking about."

**Re-resolved the plan with user input.** Six explicit decisions: high priority (freeze is festering); drop all Stream-2 stress tests (BARRIER strictly stronger per user recall); conservative Stream-2 paper trail; land Stream-1 infra as one commit + promote 4 learnings to project-level (`learnings.kb/` × 2, `technical-policy.kb/` × 2); archive branch with `archive/` prefix rather than delete; reread before extract.

## Decisions

- **Pattern named:** drafting plans from `git diff --stat` without reading the actual planning artifacts produces plausible-sounding but wrong specifics. Mitigation in this case was the user's explicit attribution challenge; without it, the bad specifics would have shipped.
- **Asymmetric confidence calibration:** when summarizing work where some content is mine and some is from external sources, I default to confident phrasing for both, which under-flags my own inferences. The right asymmetry is the opposite: flag own-generated specifics; trust source-attributed specifics.
- **Provenance audit as banner section:** the kb file now carries a `## Provenance audit` section listing user-resolved decisions, authoritative sources, and which earlier-draft claims were wrong. Pattern worth reusing on any plan-drafted-before-reading-source.

## Next Session

Execute the drain per `.claude/todo.kb/2026-05-19-000-drain-too-many-changes-freeze.md`. Phase 1 reread first (BARRIER 002/003/004 mapping verification + closure devlog skim), then Phase 2 extraction (2 commits: incubator infra; promoted learnings), then conservative Phase 3 (probably just the closure devlog if anything), then Phase 4 (archive branch, remove worktree). `.claude/focus.md` is re-aimed at the drain kb so the next session loads it via the `CLAUDE.md` `@-include` automatically.
