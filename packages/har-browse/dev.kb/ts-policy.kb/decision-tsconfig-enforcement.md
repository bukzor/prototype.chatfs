# Enforce strip-types-only policy via tsconfig

The policy in `decision-strip-types-only.md` is enforced mechanically by the
package `tsconfig.json`:

```json
{
  "compilerOptions": {
    "erasableSyntaxOnly": true,
    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "allowJs": true,
    "checkJs": false,
    "noEmit": true,
    "strict": true,
    "module": "nodenext",
    "target": "esnext",
    "moduleResolution": "nodenext"
  },
  "include": ["src/**/*.mjs", "src/**/*.ts", "tests/**/*.mjs", "tests/**/*.ts"]
}
```

## Why these flags

- **`erasableSyntaxOnly: true`** (TypeScript 5.8+) — the purpose-built flag
  for this policy. Rejects enum, namespace, parameter properties, and other
  transform-types-requiring constructs at typecheck time. With it, the policy
  becomes a build-time gate, not a convention.
- **`verbatimModuleSyntax: true`** — forces explicit `export type { Foo }`
  for type-only exports. Closes the gotcha documented in
  `gotcha-type-only-re-export.md`.
- **`isolatedModules: true`** — ensures every file is independently
  transpilable, which is exactly what Node's per-file strip-types pipeline
  requires.
- **`allowJs: true`, `checkJs: false`** — include `@ts-check`'d `.mjs` files
  in the typecheck pass, but per-file opt-in (not blanket).
- **`noEmit: true`** — tsc is a checker only; runtime is Node's strip-types.

## Wiring

Add to `package.json`:

```json
"scripts": {
  "typecheck": "tsc -p ."
}
```

Then `pnpm typecheck` in CI. Failed typecheck = failed build.
