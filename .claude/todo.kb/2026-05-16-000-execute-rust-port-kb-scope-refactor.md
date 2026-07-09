---
managed-by: Skill(llm-subtask)
blocked-by:
  - packages/har-browse/dev.kb/rust-port.kb/scope-audit.md
  - ~/.claude/sessions.kb/rust-port-kb-scope-refactor.md
supersedes-question-from: 2026-05-13-000-place-rust-port-kb-at-proper-home.md
cost-benefit-sweh:
  timebox:
    "@value": 4.0
    rationale: |
      9 sequenced mechanical steps spanning workspace + 2 future packages
      + transient work area. Realistic execution is staged across 3-4
      commits. Beyond 4h, splitting the plan further is mandatory.
  benefit-2w:
    "@value": 5.0
    rationale: |
      Hard blocker for commits 0750/1000/1050 (write durable contracts
      that need the target homes). Also unblocks polyglot package naming
      sweep and the chatfs todo rollup. Strong multiplier.
---

# Execute the rust-port kb scope refactor

**Priority:** Medium-high (must land before commits `0750`/`1000`/`1050`, which write durable contracts needing the target homes)
**Complexity:** Medium (mechanical, but spans 3 scopes — workspace, two future packages, transient work-area)
**Context:** Per-file content audit complete (2026-05-15); 4 open questions resolved; stress-test pass complete. See `packages/har-browse/dev.kb/rust-port.kb/scope-audit.md` for full audit and `~/.claude/sessions.kb/rust-port-kb-scope-refactor.md` for resolved questions + corrections.

## Plan (9 steps, sequenced)

1. **Create empty skeletons** for the two future Rust packages.
   - `packages/rs-playwright-lite/{CLAUDE.md, README.md, design.kb/, dev.kb/, adr/}` (each `.kb/` gets a CLAUDE.md). `design.kb/` stays empty until commit 1300.
   - `packages/rs-har-browse/{CLAUDE.md, README.md, design.kb/, dev.kb/, adr/}`. `design.kb/` stays empty until commit 1300 (when the existing `packages/har-browse/design.kb/` moves in).
   - Register both as Cargo workspace members in root `Cargo.toml`.
   - Empty `src/lib.rs` + `Cargo.toml` per crate.

2. **Create workspace-root `dev.kb/`** with a `CLAUDE.md` describing its purpose. Currently single occupant (rust-port); future workspace-spanning dev work has a home.

3. **Write the promoted durable docs:**
   - `docs/dev/adr/2026-MM-DD-port-har-browse-to-rust.md` (from `decisions.kb/port-to-rust.md` + charter Why/Success/Out-of-scope)
   - `docs/dev/adr/2026-MM-DD-polyglot-package-dir-naming.md` (Q4 convention)
   - `docs/dev/adr/2026-MM-DD-rust-port-work-area-location.md` (records workspace `dev.kb/` choice + considered alternatives, per stress-test WAL transparency requirement)
   - `docs/dev/background.kb/rust-chromium-automation.md` (distilled from `ecosystem-survey.md` — CfT, chrome-launcher npm, chromiumoxide, non-fits, combination gap)
   - `docs/dev/background.kb/chrome-headed-gotchas.md` (distilled from `unknown-unknowns.md` — SingletonLock, first-run prefs, process tree, stderr noise, breakpad)
   - `docs/dev/technical-policy.kb/policy-defer-with-runtime-assertion.md` (Q2)
   - **Promote** `docs/dev/technical-policy.kb/policy-safe-automation-boundary.md` to `.md`+`.kb/` pair with 4 facets (Q3):
     - `consent-via-explicit-sync.md`
     - `headed-only-with-human-terminator.md`
     - `no-bot-detection-evasion.md` (encompasses auth-via-cookie framing)
     - `per-mount-profile-isolation.md`
   - `packages/rs-playwright-lite/design.kb/two-crate-split.md` (from `crate-architecture.md` + charter Strategy)
   - `packages/rs-playwright-lite/design.kb/out-of-scope.md` (no headless, no crates.io publish, no bot-detection)
   - `packages/rs-playwright-lite/design.kb/known-limitations.md` (the 3 deferred items from `assertion-strategy.md`; each cites the WS-pol)
   - `packages/rs-playwright-lite/adr/2026-MM-DD-dependency-choices.md` (chosen + rejected; cross-refs WS-bg)
   - `packages/rs-playwright-lite/adr/2026-MM-DD-vendor-default-flags.md` (the vendor-vs-submodule decision)
   - `packages/rs-playwright-lite/dev.kb/known-issues.md` (chromiumoxide #228/#280/#312, CfT arm64 caveat)

4. **Move the work-area** from `packages/har-browse/dev.kb/rust-port.{md,kb}/` to workspace-root `dev.kb/rust-port.{md,kb}/`.

5. **Update commit-docs' `Refs:`** to point at the new permanent homes.

6. **Stub emptied source files** with one-line redirects (do not delete). Stress-test correction: stubs persist until commit 1300 sweep.

7. **Refresh `documentation-conventions.md` table** to reflect the new layout. Do this once at the end, not during iteration.

8. **Update discoverability:**
   - `packages/har-browse/dev.kb/CLAUDE.md` — remove `rust-port.kb/` collection mention (or change to "moved to workspace `dev.kb/`").
   - Root `CLAUDE.md` — point at the new workspace `dev.kb/` and at the rs- packages.
   - `packages/har-browse/CLAUDE.md` — note port in progress; point at the work-area's new location.

9. **Commit 1300 sweep** (deferred; fires when commit 1300 lands):
   - Move `packages/har-browse/design.kb/` → `packages/rs-har-browse/design.kb/` (the design.kb describes the *role*, not the language).
   - Remove all of `packages/har-browse/` (Node implementation retired).
   - `rm -rf` the transient work-area at workspace-root `dev.kb/rust-port.{md,kb}/`.

## Acceptance

- [ ] Skeletons exist; `cargo build` from workspace root still passes.
- [ ] Workspace-root `dev.kb/` exists with CLAUDE.md.
- [ ] All durable promoted docs exist at their target homes (~13 files).
- [ ] Work-area lives at workspace-root `dev.kb/rust-port.{md,kb}/`.
- [ ] All commit-docs' `Refs:` resolve to existing files.
- [ ] Emptied source files contain stub redirects (until 1300).
- [ ] `documentation-conventions.md` table matches reality.
- [ ] Root + package `CLAUDE.md` files point at correct new homes.
- [ ] (1300, deferred) design.kb migrated, transient work-area swept, Node implementation retired.

## Conditional follow-up

- **Pre-1300 Notes re-audit:** Before commit 1300 sweep, re-audit `commits.kb/*.md` `## Notes` sections. Notes accumulate during commit work and may contain content that should be promoted to durable docs rather than swept. See stress-test "Skeptic concession with genuine effort" in session file.

## Sequencing notes

- Steps 1-3 can land as a stack of commits.
- Steps 4-5 are coupled (move + Refs update); do them in one commit.
- Steps 6-8 are mop-up; one commit each or grouped.
- Step 9 is months-out (fires when commit 1300 lands).
- No destructive operations until step 6 (stubbing, not deletion); full deletion at step 9 only.

## Additional decisions layered on top (2026-05-21 meta-planning session)

Today's session evolved several of this plan's resolutions without
replacing them. Refer to workspace `.claude/decision.kb/` for the
canonical decisions; each item below cross-references.

- **Schema home (Q1 evolution):** Schemas live at
  `packages/rs-har-browse/schema/`, not `design.kb/`. Filename
  convention: `<stem>.jsonschema.yaml` matching the validated stream.
  Diagnostic events go in a *separate* stream with its own schema. See
  `.claude/decision.kb/{schema-home-and-naming,bb1-is-har-browse,separate-diagnostic-stream}.md`.
  Step 1 should add `schema/` to the `packages/rs-har-browse/` skeleton.
- **Whitehat rename (Q3 addition):** When executing Step 3's
  "Promote `policy-safe-automation-boundary.md`" item, *also* rename to
  `policy-whitehat-automation-boundary.md`. "Safe" is too ambiguous;
  "whitehat" specifies the non-adversarial security stance. See
  `.claude/decision.kb/rename-safe-to-whitehat-automation-boundary.md`.
- **Defer-and-runtime-assert dual home (Q2 addition):** Step 3 plans
  `docs/dev/technical-policy.kb/policy-defer-with-runtime-assertion.md`.
  Today the same principle also lives at
  `.claude/principle.kb/defer-and-runtime-assert.md`. Either is
  acceptable as canonical; the other becomes a cross-link. Decide at
  execution time.
- **Threat-model reframe (sibling to Q3):** The rust-port-side
  `packages/har-browse/dev.kb/rust-port.kb/facts.kb/threat-model.md`
  becomes a decision + consequence doc (the *decision* is
  "har-browse is an interactive single-user tool"; the *consequences*
  are the headed-only / no-stealth list). Sibling to the 4-facet
  policy promotion, not a replacement. See
  `.claude/decision.kb/interactive-single-user-usage.md`.

## Adjacent follow-up (not part of this plan)

- Pre-port testing infrastructure (schema design, blackbox conversion,
  baseline capture, mutation walk, diagnostic emission) →
  `~/.claude/sessions.kb/har-browse-rust-port-pre-port-infrastructure.md`.
- Workspace role-keyed kb adoption considerations →
  `<repo-root>/.claude/sessions.kb/dev-kb-five-collection-pattern.md`.
