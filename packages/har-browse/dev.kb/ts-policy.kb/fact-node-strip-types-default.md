# Node 22 strips TS types by default

Node 22 runs `.ts` files unflagged: `--experimental-strip-types` is on by
default, processing TS source by removing type annotations.

## Verification

Tested in Node 22.21.1:

```bash
# Default mode (strip-types on)
$ node trash/ts-shebang-test.ts  # file uses `interface`, generics, type args
44

# Control: same file with strip-types disabled
$ node --no-experimental-strip-types trash/ts-shebang-test.ts
SyntaxError: Unexpected identifier 'Pair'
```

The `--no-experimental-strip-types` flag exists as an opt-out, confirming
strip-types is the default.

## Surprising side-effect

`node -e` also strips types in this mode:

```bash
$ node -e 'const x: number = 42; console.log(x);'
42

$ node --no-experimental-strip-types -e 'const x: number = 42'
SyntaxError: Missing initializer in const declaration
```

People who think of `node -e` as a raw JS evaluator get the wrong answer
about what is/isn't valid ES — anything with type annotations runs, even
though it's not legal ECMAScript.

## Implication

`#!/usr/bin/env node` is the right shebang for `.ts` files. No special
runner required, no flags needed (under the strip-types-only policy in
`decision-strip-types-only.md`).
