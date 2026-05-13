# --experimental-transform-types is a strict superset of strip-types

The two flags share a single code path with last-flag-wins ordering.
Transform-types subsumes strip-types behavior.

## Verification

```bash
# no-strip first, then transform-types: transform wins
$ node --no-experimental-strip-types --experimental-transform-types 01-enum.ts
0 Red
(ExperimentalWarning: Transform Types is an experimental feature...)

# transform-types first, then no-strip: no-strip wins
$ node --experimental-transform-types --no-experimental-strip-types 01-enum.ts
SyntaxError: Unexpected reserved word
```

Verified in Node 22.21.1.

## Three states (not four)

| State | Flag combination | Coverage |
|---|---|---|
| Off | `--no-experimental-strip-types` (last) | Pure ES only |
| Strip-types | default, or strip-types flag last | Type erasure |
| Transform-types | `--experimental-transform-types` (last) | Erasure + emit-runtime constructs |

The combination `--no-strip-types --transform-types` is meaningful but
redundant: equivalent to just `--experimental-transform-types`.

## Implication

There's no "strip-types only, refuse transform-types behavior" mode. The
discipline is enforced at *source* level (via `erasableSyntaxOnly` in
tsconfig — see `decision-tsconfig-enforcement.md`), not at runtime flags.
