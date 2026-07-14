---
managed-by: Skill(llm-subtask)
related-effort: 2026-07-13-000-module-shape-refactor.md
cost-benefit-sweh:
  timebox:
    "@value": 2.0
    rationale: >
      One shared skeleton (select Network.responseReceived by URL regex →
      body → string-guard → fromjson → optional flatten) covers all 6
      `.jq` filters; 3 of the 4 `.sh` scripts collapse into the existing
      `capture()`/`run_pluck()` Python pattern with no new logic. Only
      `chatfs_claude_conversation_url_trash.sh` (find + xargs + `rmdir -p`
      symlink cleanup) needs real translation care.
    confidence: tentative
  benefit-2w:
    "@value": 0.5
    rationale: >
      Enabling, not user-visible on its own: drops `jq` as a runtime
      dependency and lets `000`'s per-family move be a pure mechanical
      file move (no new logic written mid-move) whenever it reaches each
      family. No payoff if `000` never lands.
    confidence: tentative
---

# Port `.jq`/`.sh` pipeline scripts to Python

**Priority:** Medium — enables a cleaner `000`, not independently urgent.
**Complexity:** Low
**Context:** Extracted 2026-07-14 from `000-module-shape-refactor`'s
Implementation Steps, where it was decided in place but not yet done. Can
run against the *current* flat, sibling-importing layout — doesn't need
`000`'s package-tree decision, so it isn't `blocked-by` it. Independently
completable, same tier as `002-path-ownership-contract-v1` and the
incubator's atomic-regeneration todo, both in flight concurrently as of
2026-07-14 — a candidate for a third parallel agent if wanted.

## Problem Statement

6 `chatfs_*_pluck.jq` filters and 4 `.sh` scripts (3 trivial index-browse
wrappers + 1 conversation-trash cleanup) are the last non-Python pieces of
the pipeline. They work, but: `jq` is an extra runtime dependency, the
`.sh` wrappers duplicate a pattern (`har-browse | tee | pluck`) that
`chatfs_layout.py`'s `capture()`/`run_pluck()` already solves in Python
for conversation-browse, and neither language is exercised by the
project's Python test suite or type checker.

## Proposed Solution

- One shared helper (home: `chatfs_layout.py`, or its post-`000` successor
  `chatfs/layout.py`) — an `iter_responses_matching(cdp_lines, url_pattern)`-
  style generator implementing the common skeleton: filter CDP jsonl
  records to `Network.responseReceived` events whose response URL matches
  a regex, yield the parsed JSON body (skipping empty/non-string bodies).
- Each of the 6 `*_pluck.jq` becomes a short Python function built on that
  helper, keeping its per-provider reshaping (`aistudio`'s `.[0][]`
  flatten, `aistudio` conversation's `prompts/`-prefix guard + `.[]`
  flatten) as a few lines of trailing logic.
- The 3 `*_index_browse.sh` wrappers (`har-browse URL | tee CDP |
  pluck.jq`) fold directly into the existing `capture()`/`run_pluck()`
  call shape already used by conversation-browse — no new logic.
- `chatfs_claude_conversation_url_trash.sh` ports with `pathlib`/
  `shutil.move`, preserving `rmdir -p`'s stop-at-first-nonempty-ancestor
  climb explicitly (no direct stdlib equivalent).

## Implementation Steps

- [ ] Write `iter_responses_matching` (or equivalent) in `chatfs_layout.py`,
      with a test against a captured `.data/cdp.jsonl` fixture.
- [ ] Port the 6 `*_pluck.jq` filters to Python functions using it; delete
      the `.jq` files as each lands.
- [ ] Fold the 3 `*_index_browse.sh` wrappers into `capture()`/
      `run_pluck()` call sites; delete the `.sh` files.
- [ ] Port `chatfs_claude_conversation_url_trash.sh`; delete it.

## Success Criteria

- [ ] No `.jq` or `.sh` files remain in the incubator directory.
- [ ] `jq` and shell are no longer runtime dependencies of the pipeline
      (only `har-browse`/Chromium remains external).
- [ ] Full test suite + basedpyright clean.
