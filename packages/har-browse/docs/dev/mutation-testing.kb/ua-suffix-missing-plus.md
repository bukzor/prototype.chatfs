---
status: done
---

# `user-agent.mjs`: SUFFIX drops the `+` before homepage

The `(+URL)` convention signals "contact URL" to operators reading
access logs. Drop the `+` and the parenthetical reads as a generic
annotation; tooling that greps for `(+http` to identify self-reporting
clients misses this tool's traffic.

## Injection

`src/user-agent.mjs`:

```diff
-const SUFFIX = `${pkg.name}/${pkg.version} (+${pkg.homepage})`;
+const SUFFIX = `${pkg.name}/${pkg.version} (${pkg.homepage})`;
```

## Test Coverage

`src/user-agent.test.mjs` tests 8, 9, 10, 14: each computes the
expected UA against the test's own SUFFIX (`(+...)` form) and asserts
`assert.equal`. Drop the `+` in production and the equality fails on
the parenthetical.
