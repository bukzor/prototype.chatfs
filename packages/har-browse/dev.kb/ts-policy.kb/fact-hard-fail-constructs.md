# TS constructs that fail even with --experimental-transform-types

Some TS source forms produce errors regardless of the `--experimental-*`
flag set in Node 22.21.

## Legacy `@decorator` syntax

```ts
class Foo { @log method() { return 1 } }
```

Fails with `SyntaxError: Invalid or unexpected token` in both strip-types
and transform-types modes. No Node flag enables legacy TS-experimental
decorators.

Stage-3 standard decorators (TC39) may behave differently — not verified.

## JSX in `.tsx` files

```tsx
const el = <div className="x">hello</div>;
```

Fails with `SyntaxError: Unexpected token '<'`. JSX requires a real
bundler/transform; no Node flag is sufficient. If JSX is needed, the
package needs a build step or `tsx` runtime.

## Ambiguous type-only re-export

```ts
type MyType = { n: number };
export { MyType };  // FAILS: "Export 'MyType' is not defined in module"
```

Strip-types is a syntactic pass — it can't tell whether `MyType` has a
runtime value. The fix is to write `export type { MyType }` explicitly.

This case is detailed in `gotcha-type-only-re-export.md` and is enforceable
at typecheck time via `verbatimModuleSyntax: true` in tsconfig.

## Implication

Even with the most permissive flag set, three classes of TS source remain
unsupportable in Node:

- Decorators (legacy)
- JSX
- Type-only re-exports without `export type`

The first two we avoid entirely. The third is preventable via tsconfig.
