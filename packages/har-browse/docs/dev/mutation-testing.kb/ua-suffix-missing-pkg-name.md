---
status: done
---

# `user-agent.mjs`: SUFFIX omits the package name

`${pkg.name}/${pkg.version}` is the `ToolName/Version` half of the
self-identifying SUFFIX. Drop `pkg.name` and the SUFFIX becomes just
`/${pkg.version} (+...)` — operators can't tell which tool is making
requests.

## Injection

`src/user-agent.mjs`:

```diff
-const SUFFIX = `${pkg.name}/${pkg.version} (+${pkg.homepage})`;
+const SUFFIX = `/${pkg.version} (+${pkg.homepage})`;
```

## Test Coverage

`src/user-agent.test.mjs` tests 8, 9, 10, 14 — full-string equality
against the test-computed SUFFIX (which includes `pkg.name`) fails
when production omits it.
