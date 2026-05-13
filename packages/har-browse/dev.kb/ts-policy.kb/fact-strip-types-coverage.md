# What strip-types supports and rejects

Empirical results from running `trash/ts-features/*.ts` under default
Node 22.21 (strip-types on, transform-types off).

## Supported (pure type erasure)

These constructs disappear at parse time, leaving valid JS:

- Type annotations on variables, parameters, returns
- `interface` declarations
- `type` aliases
- Generics (declaration and call-site type args)
- `as` type assertions
- `satisfies` operator
- `import type` / `export type`
- `declare` statements
- Union/intersection types, conditional types, mapped types, template
  literal types
- `keyof`, `typeof`, `infer`

## Rejected with `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX`

These emit runtime code; the stripper refuses with a clear error message:

- `enum`, `const enum` — emit object literals with reverse mappings
- `namespace` — emits IIFE pattern
- Class parameter properties (`constructor(public x: T)`) — emits `this.x = x`
- `import x = require(...)` — emits CommonJS-style code

All four are recoverable with `--experimental-transform-types`, but doing so
is rejected by policy (`decision-strip-types-only.md`). The right move when
these fail is to rewrite the source — use `as const`, ES modules, explicit
field declarations, named imports.

## Hard fails

Some constructs fail regardless of flag — see `fact-hard-fail-constructs.md`.
