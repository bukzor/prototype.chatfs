---
status: done
---

# `cache.mjs`: `mkdirSync` removed entirely

`cachePath` advertises that the returned directory exists. Drop the
`mkdirSync` call and callers writing into the returned path hit ENOENT.
Distinct from `cache-no-recursive-mkdir.md`, which still creates leaves
when the parent already exists; this mutation creates nothing.

## Injection

`src/cache.mjs`, in `cachePath()`:

```diff
   const path = join(ROOT, namespace, segments);
-  mkdirSync(path, { recursive: true });
   return path;
```

## Test Coverage

`src/cache.test.mjs` tests 1-4: each ends with
`assert.equal(existsSync(result), true)` — fails when nothing is
created. Also fails `src/user-agent.test.mjs` tests 8, 9, 10, 14 where
the test seeds via `writeFileSync(expectedCacheFile(...), ...)`; that
write throws ENOENT when the parent dir doesn't exist.
