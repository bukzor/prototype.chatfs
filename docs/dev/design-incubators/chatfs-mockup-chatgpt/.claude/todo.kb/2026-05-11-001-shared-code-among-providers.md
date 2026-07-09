---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    '@value': 2
    confidence: tentative
    rationale: |
      Extract shared lib (chatfs_layout.py initial home, possibly promote to packages/chatfs-core/). Touch each provider's scripts; verify end-to-end against all providers. ~1.5-2.5 SWEh once triggered. Tactical capture in todo.md parity ladder already encodes the immediate moves.
  benefit-2w:
    '@value': 0.5
    confidence: tentative
    rationale: |
      Strategic decision file; cross-provider abstraction question. Direct 2w value is design clarity (when/where), not code landing.
---

# shared code among providers

**Priority:** Low (signal weak at two providers; load-bearing once
three exist)
**Complexity:** Medium — touches all providers' scripts and `place_meta`
boundary; correctness verified by all-providers end-to-end.

**Context:**
- User note (2026-05-11): *"once we have claude-code we have three
  'providers' and we can start to factor commonalities into 'lib'
  shared code."*
- `todo.md` "Claude provider — parity ladder → Refactor" — tactical
  capture: `chatfs_chatgpt_layout.py` + `chatfs_claude_layout.py` →
  `chatfs_layout.py`; promote `provider-plugin-model.md` to a real
  incubator entry.
- `chatfs_chatgpt_layout.py` — already-partial shared primitives
  (`IndexItem`, `safe_filename`, `time_dir_for`, `place_meta`,
  symlink placement, `.data/` exhaust policy).
- `../../../../technical-policy.kb/` — opaque-extractor boundary; lib
  must respect it (extractors stay per-provider).

## Scope

Factor provider-agnostic helpers into a shared module. Each provider
keeps only its extractor (HAR-pluck, CDP+pluck, JSONL-read) and its
locator parser; splat, render, and layout primitives are shared.

## Strategic Decisions Pending

- **When to extract:** ~~user-stated trigger is *three providers*~~
  **decided 2026-07-05: extracted**, triggered by the third provider
  (aistudio) landing.
- **Lib home:** ~~incubator-local vs. `packages/chatfs-core/`~~
  **decided 2026-07-05: incubator-local.**
- **What moves vs. stays:** `chatfs_chatgpt_layout.py` is a starting
  point but not necessarily the boundary — provider-specific code
  may still hide in it.

## Open Questions

- Does the rule-of-three logic actually hold here, or is two providers
  enough signal because of how shared the chatgpt and claude.ai
  pipelines already look? (Revisit when claude.ai parity lands.)
- Does the eventual lib justify promotion out of the incubator (into
  `packages/chatfs-core/`), or stay incubator-local until BB2/BB3
  stabilize?

## Notes

Tactical capture already exists in `todo.md` parity ladder. This
strategic file holds the *cross-provider abstraction* question
separately — the tactical line will execute it; this file justifies
*when* and *where*.

Before starting the extraction, read
[cross-provider data-flow drift](2026-07-03-000-cross-provider-data-flow-drift--pre-unification-fixes-vs-unification-scope.md)
§ "Solve by unification — do NOT fix in place" — five requirements
(shared `capture()`, persist every pluck output, endpoint cross-check
on all providers, provider-complete `<details>` wrapping, pipe-vs-
delegation decision) the shared lib must satisfy, discovered by the
2026-07-03 three-provider review.
