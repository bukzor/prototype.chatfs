---
managed-by: Skill(llm-subtask)
status: open
cost-benefit-sweh:
  timebox:
    "@value": 0.75
    rationale: |
      Same shape and size as the conversation-splat fold-in this todo
      follows on from (2 small commits, ~1h combined). har2jsonl is a
      single file plus its test; the only real cost is deciding, not
      doing.
    confidence: unsure
  benefit-2w:
    "@value": 0.5
    rationale: |
      Closes the last piece of an already-decided reversal
      (module-shape-refactor.md's chatgpt-splat carve-out, expired
      2026-08-16); mostly tidiness, not a blocker for anything.
    confidence: unsure
---

# bukzor.chatgpt-export package fate

**Priority:** Low
**Complexity:** Low
**Context:** 2026-08-16, `chatgpt conversation splat` was folded into
`chatfs.provider.chatgpt.conversation.splat` (the "stays external"
carve-out in `docs/dev/design.kb/040-design.kb/package-division.md` and
the module-shape-refactor todo expired, user fiat). `bukzor.chatgpt-export`
now holds only `lib/bukzor/chatgpt_export/{json.py,har2jsonl.py,
har2jsonl_test.py}`, plus its own `pyproject.toml`. `json.py` is
`har2jsonl`'s dependency (Decimal-preserving JSON, needed for the same
sub-millisecond-timestamp reason `chatfs.provider.chatgpt.json` exists).

## Problem Statement

`har2jsonl.py` converts a manually-exported `.har` file to jsonl. It
predates chatfs-cli's har-browse/pluck capture pipeline (added
2026-03-10, four months before the provider architecture existed) and is
unreferenced by any current pipeline path or doc (`how-to-chatfs.md`
never mentions it) -- confirmed via repo-wide grep during the splat
fold-in. Its package, `bukzor.chatgpt-export`, now exists solely to host
this one unreferenced file plus its own JSON helper.

## Current Situation

- `packages/bukzor.chatgpt-export/lib/bukzor/chatgpt_export/`:
  `json.py`, `har2jsonl.py`, `har2jsonl_test.py`.
- Console script `chatgpt-har2jsonl` still installed (chatfs-cli's own
  `chatgpt-splat` entry was removed in the fold-in; this one wasn't
  touched).
- Root `pyproject.toml`'s `[dependency-groups] dev` still lists
  `bukzor-chatgpt-export[dev]` -- needed only for `har2jsonl_test.py`'s
  `pytest` dependency now (the typesafety extras moved to `chatfs-cli`
  with the splat test).

## Open Questions

- Does anyone still use `chatgpt-har2jsonl` standalone (a manual HAR
  export, outside the browser-automation capture path)? If yes, the
  package should stay as-is -- it's doing real, still-used work.
- If no: fold `har2jsonl.py` into `chatfs.provider.chatgpt` too (same
  treatment as splat: pick a home, e.g.
  `chatfs.provider.chatgpt.har2jsonl`, port the test, wire an entry
  point) and delete `packages/bukzor.chatgpt-export/` entirely -- or
  just delete both without porting, if the manual-HAR-file path is
  judged genuinely dead rather than merely unreferenced by the
  *current* browser-driven capture path.

## Proposed Solution

Pending the open question above. If retiring: same two-commit shape as
the splat fold-in (port + wire, then remove the empty shell + prune
`[dependency-groups]`/`[tool.uv.workspace]` references), keeping each
commit independently green.

## Success Criteria

- [ ] Decision recorded (keep standalone / fold in / delete outright)
- [ ] If not "keep standalone": `packages/bukzor.chatgpt-export/`
      removed from `pyproject.toml` workspace members and
      `[dependency-groups]`; `uv.lock`/`uv sync` clean
- [ ] Full workspace suite green, basedpyright clean, after either path
