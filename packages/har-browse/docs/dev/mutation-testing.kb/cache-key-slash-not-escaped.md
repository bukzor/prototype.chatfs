---
status: done
---

# `cache.mjs`: don't escape `/` in cache key values

Hive-style keys with `/` in the value (e.g. a UA containing a path
fragment, or a future caller passing a URL-like value) create
unintended subdirectories. Two distinct values that differ only in
where slashes fall would collide; a single value with a trailing `/`
would create a sibling dir.

## Injection

`src/cache.mjs`, in `escape()`:

```diff
-  return s.replaceAll("/", "\\");
+  return s;
```

## Test Coverage

`src/cache.test.mjs`: "hive cache-key value with '/' must be escaped
so it stays one path segment" — equality assertion pins the exact path
shape, so any change to the encoding (or removal of escaping) fails.

While here, added five neighbor unit tests covering the rest of
`cachePath`'s contract: string-key path shape, hive-key shape, the `=`
and NUL assertions on keys, and the NUL assertion on values. Test
lives colocated at `src/cache.test.mjs`; wired `src/**/*.test.mjs`
into the `test` / `test:unit` scripts so node:test discovers it.
