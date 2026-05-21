---
status: done
---

# `cache.mjs`: hive segments joined with `&` instead of `/`

The hive encoding maps `{k1:v1, k2:v2}` to nested directories
`k1=v1/k2=v2/`. Join with `&` and the whole hive collapses into one
path segment `k1=v1&k2=v2/`, breaking nesting — different cache shape,
and the path on disk doesn't match what callers compute when they
predict the location.

## Injection

`src/cache.mjs`, in `cachePath()`:

```diff
-          .join("/");
+          .join("&");
```

## Test Coverage

`src/cache.test.mjs` test 2 ("hive key joins as k=v segments") —
multi-key fixture pins the path to `.../ns/a=1/b=2`; with `&` join it
becomes `.../ns/a=1&b=2`, equality fails. Single-key tests (3, 4) and
the UA test (9) don't catch this because they only exercise one
segment or because both seeder and reader use the same encoder.
