# 2026-05-19: har-browse mutation-testing kb established

Post-hoc TDD session on `packages/har-browse/` via
Skill(mutation-testing). Stood up the kb, drove leaf-first through 22
planned mutations, paused for fresh-session continuation.

## Focus

Apply Skill(mutation-testing) to har-browse. Skeleton first, then
smallest leaves (`cache.mjs` → `user-agent.mjs` → `inject.mjs` →
`capture.mjs`).

## What Happened

**KB stood up at `packages/har-browse/docs/dev/mutation-testing.kb/`**
— CLAUDE.md plus 22 mutation entries, each with frontmatter
(`status:` enum) + Description + `## Injection` (the exact diff to
make). Planning step listed mutations verbally in conversation before
reading existing tests, per the skill's
"independent-reasoning-first" principle.

**Final tally: 15 done / 6 gap / 1 todo.** Done batch:

- 3 cache.mjs (cache-key-slash-not-escaped, cache-key-equals-assertion-removed, cache-no-recursive-mkdir) caught by new
  `src/cache.test.mjs` (6 unit tests).
- 3 user-agent.mjs (suffix-missing-from-ua, cache-key-missing-revision, cache-key-missing-headless) caught by new
  `src/user-agent.test.mjs` (3 tests; pre-seeds cache to avoid real
  browser launches).
- 3 inject.mjs (dataset-clicked-value-wrong by existing
  persistent_injection.spec.mjs; inject-overlay-no-idempotency and
  done-button-not-once via 2 new tests added to that file).
- 6 capture.mjs (3 BARRIER mutations via barrier_smoke.spec.mjs; 2 body
  mutations via har.spec.mjs; done-dataset-typo via test timeout).

**6 gaps documented with the fixture each would need to convert to
done.** Notable: `barrier-snapshot-not-frozen` is a *phantom mutation*
— `Promise.allSettled([...inFlight])` and `Promise.allSettled(inFlight)` are semantically identical (allSettled iterates
synchronously at call time). The mutation rationale was wrong on
inspection; recorded as gap with explanation. Similar reassessment for
`body-attached-after-loading-finished`: chrome-har joins RR+LF by
requestId and tolerates either order, so the original "chrome-har may
drop the entry" premise didn't hold up.

## Decisions

- **Colocated tests over `tests/` directory** — at user request,
  switched unit tests from `tests/cache.test.mjs` to
  `src/cache.test.mjs`. Mid-stream rationale: in JS-world both
  `.test.mjs` and `_test.mjs` work; `.test.mjs` is more idiomatic.
  Integration tests (BARRIER spans capture + inject + cdp_to_har) stay
  in `tests/` because they don't belong to one source file. Updated
  `package.json` `test` and added `test:unit` to glob
  `'src/**/*.test.mjs' 'tests/*.test.mjs'`.
- **`{ once: true }` testable via CDP `DOMDebugger.getEventListeners`**
  — the click handler does idempotent work, so behavior-observation
  routes are weak. Direct listener-count assertion via CDP is the
  least-intimate way to assert the option without modifying production
  code.
- **Phantom mutations get `gap` with explanation, not deletion** —
  recording the analysis is more useful than removing the entry; the
  reasoning trail prevents re-litigation.

## Next Session

- Drive `events-subscribed-after-cdp-attach` (the one remaining
  `todo`). Hypothesis: `har.spec.mjs` catches it via missing early-
  navigation RRs. ~5 min.
- Convert 5 of the 6 gap entries to `done` by adding the fixtures each
  needs. (The 6th, `barrier-snapshot-not-frozen`, is a phantom.) Per-
  entry fixture sketches are in the kb's `## Test Result` sections;
  total ~1 hour.

## See Also

- Session record: `~/.claude/sessions.kb/har-browse-mutation-testing.md`.
- Local todo: `packages/har-browse/.claude/todo.md` "Mutation testing"
  section.
- KB: `packages/har-browse/docs/dev/mutation-testing.kb/CLAUDE.md`.
- Skill: `~/.claude/skills/mutation-testing/SKILL.md`.
