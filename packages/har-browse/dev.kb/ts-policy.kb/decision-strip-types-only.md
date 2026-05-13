# Policy: write only strip-types-compatible TS

When `.mjs` files are renamed to `.ts` (or new `.ts` files are added),
restrict source to constructs that work under default Node 22+ behavior
(`--experimental-strip-types` mode). **Do not enable
`--experimental-transform-types`.**

## What this excludes

- `enum`, `const enum` — use `as const` object literals + union types
- `namespace` — use ES modules
- Class parameter properties (`constructor(public x: T)`) — declare fields explicitly
- `import x = require(...)` — use `import * as x from "..."` or named imports
- Legacy `@decorator` syntax — avoid entirely
- JSX in `.ts` / `.tsx` files (would require a real bundler)
- `export { Foo }` where `Foo` is type-only — write `export type { Foo }`

## Rationale

- **TC39 alignment.** Stage 1 "Type Annotations" proposal aligns with
  strip-types semantics (annotations as comments). Transform-types constructs
  are explicitly out of scope and won't become native JS. Strip-types
  discipline is forward-compatible with possible future JS-native types.
- **No warning noise.** Strip-types is silent at default; transform-types
  prints `ExperimentalWarning` to stderr on every invocation — noise that
  matters in CI logs and streaming-JSONL output.
- **Path to non-experimental.** Strip-types is the simpler, more conservative
  feature and the likelier candidate to lose `--experimental-` first.
- **Deprecated-style constructs.** The TS team itself recommends against
  `enum` (prefer `as const`), `namespace` (deprecated), and parameter
  properties (controversial) in modern code.
- **Clean shebangs.** `#!/usr/bin/env node` works unchanged on `.ts` under
  strip-types-only — no `tsx` devDep, no special runner.
- **Toolchain reach.** Lightweight bundlers and alternative runtimes
  (Bun, Deno) tend to support the type-erasure subset before transform-types
  semantics.

## Related

- `decision-tsconfig-enforcement.md` — mechanical enforcement via tsc
- `fact-transform-types-superset.md` — flag relationship
- `fact-strip-types-coverage.md` — what's supported / rejected
- `fact-hard-fail-constructs.md` — what no flag rescues
