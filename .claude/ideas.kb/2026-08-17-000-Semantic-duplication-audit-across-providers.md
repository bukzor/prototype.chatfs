---
managed-by: Skill(llm-subtask)
status: exploring
cost-benefit-sweh:
  timebox:
    "@value": 1.5  # pairwise LLM read of each named verb's per-provider bodies
  benefit-2w:
    "@value": 0.5  # tidiness + drift-prevention, not a blocker
---

# Semantic duplication audit across providers

## The Idea

2026-08-16's copy-paste scan (`fenced_json`/`render_details` dedup,
`chatfs.splat`) was name-based: `grep '^def '` per provider dir,
intersect names across claude/chatgpt/aistudio, triage each hit by hand.
That catches literal duplication but is blind to the same purpose living
under a different name in two providers -- nothing here would notice if,
say, one provider's icon-lookup were a `dict` and another's an
`if/elif` chain doing the same job.

Test-*name* diffing (`comm -12` across all three providers' `it_*`/
`test_*` names) was tried live as a cheap purpose-level proxy and came
back empty -- consistent with "nothing left to catch this way," but it's
also name-based and has the same blind spot one level up.

The actual gap: pairwise LLM judgment, scoped to the design.kb's named
per-provider "verbs" (splat, browse, render, pluck, massage, capture,
place) rather than the whole codebase at once (O(n²) unscoped is not
worth it). For each verb, read all three providers' implementations
side by side and judge behavioral equivalence, not textual similarity.

## Potential Benefits

- Catches the class of duplication that survives a name-based scan --
  the actual open question from 2026-08-16's session.
- A verb-by-verb read is also a cheap correctness audit for free (differences
  found are either intentional provider divergence -- worth a comment if
  undocumented -- or a real behavioral drift bug).

## Open Questions / Unknowns

- Worth automating (embedding similarity over function bodies as a
  candidate-pair filter before spending LLM judgment) or is a manual
  verb-by-verb read cheap enough at 3 providers × ~7 verbs to just do
  directly?
- Where would an extracted shared helper actually live if one's found --
  same `chatfs.splat`-style new module, or does it belong in
  `chatfs.render`/`chatfs.pluck` depending on which stage the verb is?

## Exploration Notes

Surfaced 2026-08-16 answering a direct question ("what about code that
has the same purpose but different representation?") during the
`fenced_json`/`render_details` dedup session -- see devlog
`2026-08-16-000-chatgpt-splat-folded-into-chatfs--cross-provider-render-helper-dedup.md`.
Not scoped further than naming the target (the design.kb's verb list) and
the method (pairwise read, not a text-similarity tool).

## Next Steps (if pursuing)

- [ ] Pick one verb (e.g. `browse`, likely most similar across providers
      given `url_browse.py`/`path_browse.py`'s shared orchestration
      shape) and do one pairwise read as a pilot -- decide if it's worth
      generalizing to the rest before committing to all seven.

## Lifecycle

**Status:** Exploring
