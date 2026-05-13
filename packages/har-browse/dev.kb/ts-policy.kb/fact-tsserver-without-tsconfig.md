# tsserver honors @ts-check on .mjs files without a tsconfig

The TypeScript Language Server (tsserver) — used by editors and by Claude
Code's LSP tool — resolves `@ts-check` directives in `.mjs` files even when
the project has no `tsconfig.json` and no `tsc` installed.

## Verification

Hovering at `src/capture.mjs:25:17` (the `attachCapture` function) returns a
fully typed signature with JSDoc descriptions resolved:

```
function attachCapture(page: Page, { howto }?: {
    howto?: string;
}): Promise<{
    events: AsyncIterable<CDPEvent>;
    done: Promise<void>;
}>
```

At the time of this verification, the package had:
- no `tsconfig.json` anywhere in the workspace
- no `typescript` devDep
- no `tsc` binary in `node_modules/.bin`

The LSP tool's hover succeeded anyway because the editor's tsserver loads
on demand against the file and interprets `@ts-check` independently.

## Implication: two independent layers of TS checking

| Layer | Reads `@ts-check`? | Working without tsconfig? |
|---|---|---|
| **tsserver** (LSP) | Yes | Yes |
| **tsc** (compiler/checker) | Yes | No — needs `tsconfig.json` + tsc install |

`@ts-check` alone (no tsconfig) gives editor-time benefit but zero
build-time / CI rigor. A type error would surface only when someone happens
to open the file in a TS-aware editor.

This is why `decision-migration-substeps.md` separates substep A
(tsconfig + typecheck script) from substep B (`@ts-check` rollout).
Without A, B's value is editor-only.
