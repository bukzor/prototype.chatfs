---
status: done
---

# `user-agent.mjs`: SUFFIX omits the homepage parenthetical

The `(+${pkg.homepage})` parenthetical is the contact URL. Drop it
and operators can identify the tool but have no path to the
maintainer.

## Injection

`src/user-agent.mjs`:

```diff
-const SUFFIX = `${pkg.name}/${pkg.version} (+${pkg.homepage})`;
+const SUFFIX = `${pkg.name}/${pkg.version}`;
```

## Test Coverage

`src/user-agent.test.mjs` tests 8, 9, 10, 14 — full-string equality
against the test-computed SUFFIX (which includes `(+homepage)`) fails
when production omits the parenthetical.
