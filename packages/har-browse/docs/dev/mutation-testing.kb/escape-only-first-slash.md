---
status: done
---

# `cache.mjs`: `escape()` uses `replace` instead of `replaceAll`

`escape()` exists to keep a single hive value as one path segment. With
`replace`, only the FIRST `/` is escaped; remaining slashes still split
into subdirectories. Two values that differ only in slash positions
collide silently — same bug class as `cache-key-slash-not-escaped`, just
restricted to values with ≥2 slashes.

## Injection

`src/cache.mjs`, in `escape()`:

```diff
-  return s.replaceAll("/", "\\");
+  return s.replace("/", "\\");
```

## Test Coverage

`src/cache.test.mjs`: "hive cache-key value with multiple '/'s escapes
every one" — pins `cachePath("ns-multi-slash", { k: "a/b/c" })` to a
path ending in `k=a\\b\\c`. With `replace` (first-match-only), the path
ends in `k=a\\b/c` and equality fails. The pre-existing single-slash
test passes either way; the multi-slash variant is the discriminating
fixture.
