# Re-exporting a type-only name fails under strip-types

When `export { Foo }` re-exports a name that has only a type (no runtime
value), Node's strip-types fails at module load:

```ts
type MyType = { n: number };
export { MyType };
```

```
SyntaxError: Export 'MyType' is not defined in module
```

## Why

Strip-types is a syntactic pass — it doesn't resolve identifiers. When it
sees `export { Foo }`, it leaves the export as a runtime export. If `Foo`
has no runtime value (it was a type alias / interface), Node's module
loader fails because the binding doesn't exist after stripping.

## Fix

Use `export type { ... }` explicitly:

```ts
type MyType = { n: number };
export type { MyType };
```

Or, for files that mix value and type exports:

```ts
export type { MyType };
export { aValue };
```

The `export type` form signals at the syntax level that the export is
type-only, so the stripper removes it entirely (rather than emitting a
runtime export with no backing value).

## Enforcement

`tsconfig.json` with `"verbatimModuleSyntax": true` makes `tsc` flag any
ambiguous re-export as an error at typecheck time. With CI typecheck wired
(per `decision-migration-substeps.md` substep A), this becomes a build-time
gate — the gotcha can't ship.
