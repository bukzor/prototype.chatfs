---
status: done
---

# `cache.mjs`: hive segment formatted as `v=k` instead of `k=v`

The hive encoding is `key=value/`. Swap the order in the template and
each segment becomes `value=key/`. Path layout is wholly different, and
two callers using the same keys with swapped values would no longer
collide where they should.

## Injection

`src/cache.mjs`, in the `Object.entries(key).map(...)`:

```diff
-            return `${escape(k)}=${escape(v)}`;
+            return `${escape(v)}=${escape(k)}`;
```

## Test Coverage

`src/cache.test.mjs`: tests 2 ("hive key joins as k=v segments"), 3
("slash escaped"), 4 ("multiple slashes escaped") — equality assertions
on the exact path shape catch any swap of the `k=v` segment template.
Also fails `src/user-agent.test.mjs` test 9 (revision cache key) because
the UA cache path is built via the same hive encoder.
