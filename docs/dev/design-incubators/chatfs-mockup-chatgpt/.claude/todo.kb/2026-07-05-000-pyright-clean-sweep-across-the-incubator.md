---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 2.5
    rationale: >
      16 mechanical dict/Mapping type-args across 5 files (~1h). Author's
      own note: typing the root dicts should collapse most of the
      ~170-warning cascade for free, residual narrowed with TypeGuards
      (~1h). Smoke-test each touched file against chatfs.demo/ (~0.5h).
      Genuine unknown flagged in the file's own Open Questions: if
      "pyright-clean" means zero-warnings and the cascade doesn't
      collapse as expected, this could run well over — hence tentative,
      not unsure.
    confidence: tentative
  benefit-2w:
    "@value": 0.5
    rationale: >
      Design-incubator code under active churn — 3 sibling todos in this
      same directory (aistudio-parity-ladder, cross-provider-drift,
      shared-code-among-providers) touch these same files. Real types
      reduce friction/bugs for that near-term follow-on work; not
      measured.
    confidence: unsure
  cost-of-delay-2w:
    "@value": 0.2
    rationale: >
      No external deadline; low urgency. Some momentum value — context
      is freshest right now, right after the chatfs_layout.py extraction
      that surfaced these errors.
    confidence: tentative
---

# pyright-clean sweep across the incubator

**Priority:** Medium
**Complexity:** Medium — mechanical for the errors, deeper for the warning cascade
**Context:** Follow-on from `2026-07-05-000-chatfs-mockup-chatgpt--extract-shared-chatfs-layout-py.md`
(devlog); user asked to get `basedpyright .` clean across the whole incubator
after that extraction landed.

## Approach

Bare `dict`/`Mapping` generics (`reportMissingTypeArgument`) cascade into a
much larger set of `reportUnknownVariableType`/`reportAny` warnings
downstream, since untyped dicts poison everything read out of them. Fixing
the root shape collapses the cascade for free — confirmed end-to-end on the
AI Studio provider (4 files, 0 errors/0 warnings after typing, no leftover
warnings needed separate narrowing beyond the guards below).

House pattern, applied per file:

- Give every JSON shape a `TypedDict`, not a dataclass — these are
  passthrough JSON blobs (captured API responses / jq output) that carry
  undeclared pass-through fields serialized verbatim; only fields actually
  read get declared (see `chatfs_claude_types.py`'s `ChatMessage`/`IndexItem`
  for the existing precedent).
- House every provider's types in its `chatfs_{provider}_types.py`
  container — even a shape used by only one module, for uniformity: the
  container already exists per provider, so there's no new file to justify
  keeping a type local.
- Any parsed-JSON entry point (`json.loads`/`json.load`) must go through
  `chatfs_json.loads` + a `TypeGuard` (e.g. `is_conversation`) colocated
  with its `TypedDict` in the same `_types.py`. A bare type annotation on
  an `Any`-returning call is **not** sufficient — basedpyright's
  `reportAny` specifically flags that as an unverified cast; the guard
  performing a real runtime check is what actually satisfies it.
- While a file is open for the dict fix, also clear incidental non-typing
  warnings in it (`reportUnusedCallResult`, `reportImplicitStringConcatenation`,
  …) — cheap, and leaves the touched file fully clean in one pass.
- Smoke-test each touched file against already-captured `chatfs.demo/`
  data after typing (these are splat/render files with real I/O, not pure
  refactors) — for a `json.loads`→`chatfs_json.loads` swap, diff the
  output byte-for-byte against the prior capture.

Re-run `basedpyright .` to see what's left; file-by-file counts aren't
tracked here since they drift as fixes land — the linter is the source of
truth, not this doc.

## Success Criteria

- [x] `basedpyright .` reports 0 errors, 0 warnings outside `trash/`
- [x] Each touched file's runtime behavior verified unchanged (smoke test)

## Notes

Session context: `~/.claude/sessions.kb/pyright-clean-sweep-across-the-incubator.md`.
The chatfs_layout.py extraction (commit b0665ce, 2026-07-05) is what surfaced
this — pyright was run to verify that refactor, and its pre-existing errors/
warnings in sibling files came into view.
