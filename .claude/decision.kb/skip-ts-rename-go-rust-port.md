# Skip the TS rename of har-browse; do the Rust port instead

For `packages/har-browse/`, do not pursue the `.mjs` → `.ts` rename
(TS-migration substep C per
`packages/har-browse/dev.kb/ts-policy.kb/decision-migration-substeps.md`).
Pursue the Rust port instead (per
`packages/har-browse/dev.kb/rust-port.md`).

## Why

- **Substep A is already done** via commit `148b5fa` ("enable noImplicitAny
  in tsc; close the 49 resulting holes"). Typecheck is a real CI gate now.
- **Substep B is largely captured** by `noImplicitAny`; the typed lifeline
  exists across the package's boundary surface.
- **Substep C** is described in the policy doc as "marginal over A+B;
  aesthetics + native generics + cleaner CDP types. Strictly optional."
  The Rust port supersedes all three benefits.
- **Cross-language friction with `chatfs-fuser`** is the unsolved cost the
  TS rename cannot touch. Per `rust-port.kb/decisions.kb/port-to-rust.md`,
  "fully-typed JS doesn't solve the cross-language seam."
- The recent mutation-testing pass (`docs/dev/mutation-testing.kb/`)
  sharpens the Node-side spec — which compounds with the Rust port (the
  blackbox regression gate has a sharper oracle) but not with the rename.

## Execution

The Rust port plan lives at `packages/har-browse/dev.kb/rust-port.md` and
its work-area `packages/har-browse/dev.kb/rust-port.kb/`. The `.mjs`
extension stays unchanged on the Node implementation through cutover at
commit `1300`, at which point the Node implementation is deleted.

Decided 2026-05-21.
