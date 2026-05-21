---
status: done
---

# `cache.mjs`: `escape()` drops `String(v)` coercion

`escape(v)` begins with `const s = String(v)` so non-string values
(numbers like `revision`, booleans like the explicit `String(headless)`
upstream) reach the NUL guard and `replaceAll` as strings. Drop the
coercion and a numeric value crashes on `.includes`/`.replaceAll`
("not a function"). Tests use string values; if any production caller
passes a non-string (e.g. playwright registry surfaces a numeric
revision), the bug is reachable.

## Injection

`src/cache.mjs`, in `escape()`:

```diff
-  const s = String(v);
+  const s = v;
```

## Test Coverage

`tests/tsc.test.mjs` (test 19 `tsc --noEmit (whole project)`) — `escape`
is typed `(v: unknown) => string`. Without `String(v)`, calls to
`v.includes(...)` and `v.replaceAll(...)` fail TS2339 ("Property
'includes' does not exist on type 'unknown'"). The type system catches
this before any runtime fixture would.
