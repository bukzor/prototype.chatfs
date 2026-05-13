# TS migration is three substeps, not one

Migrating har-browse from `@ts-check`'d `.mjs` to native TS factors into
three substeps with different cost/benefit profiles. Treating them as one
atomic step misweights ROI.

## A. Wire build-time typecheck (small, high-ROI prerequisite)

- Install `typescript` as devDep.
- Add `tsconfig.json` per `decision-tsconfig-enforcement.md`.
- Add `"typecheck": "tsc -p ."` to `package.json` scripts.
- Wire into CI.

**Cost:** ~20–30 minutes. **Benefit:** CI-gates the existing `@ts-check`
work. Without A, the `@ts-check` already in `capture.mjs` is editor-only.

## B. Roll out `@ts-check` to remaining .mjs files

- Per-file opt-in. Tighten any errors that surface.
- Depends on A for real rigor.

**Cost:** 1.5–3 hours. **Benefit:** typed lifeline across every boundary
file in the package.

## C. Rename `.mjs` → `.ts` (optional polish)

- Node 22 strips types from `.ts` by default; `#!/usr/bin/env node` shebangs
  work unchanged.
- Source restricted per `decision-strip-types-only.md`.
- Optionally install `devtools-protocol` for typed CDP event shapes (would
  let us drop `any` on `params` throughout `capture.mjs`).

**Cost:** 4–6 hours. **Benefit:** marginal over A+B; aesthetics + native
generics + cleaner CDP types. Strictly optional.

## Stopping points

- After **A alone**: capture.mjs's existing types are CI-gated. Best
  bang/buck.
- After **A + B**: typed lifeline across the package. Recommended terminus
  for the bewilderment-minimization goal.
- After **A + B + C**: marginal aesthetic polish; pursue only if a separate
  reason arises (e.g., importing a `.d.ts`-shipping library where JSDoc
  interop hurts).

## Related

- `decision-strip-types-only.md` — the policy that constrains substep C
- `decision-tsconfig-enforcement.md` — what substep A configures
- `fact-tsserver-without-tsconfig.md` — why `@ts-check` alone is editor-only
