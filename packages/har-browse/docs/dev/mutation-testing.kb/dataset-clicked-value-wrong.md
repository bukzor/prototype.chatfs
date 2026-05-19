---
status: done
---

# `inject.mjs`: Done click writes wrong dataset value

The page-side click handler signals capture by setting
`event.target.dataset.clicked = "true"`. Capture polls
`document.getElementById("capture-done")?.dataset.clicked === "true"`.
If the value written is anything other than the exact string `"true"`,
the poll never resolves and capture hangs until the context closes.

## Injection

`src/inject.mjs`, in the click handler:

```diff
-            e.target.dataset.clicked = "true";
+            e.target.dataset.clicked = "yes";
```

## Test Coverage

`tests/persistent_injection.spec.mjs`: "Done Capturing button survives
navigations" — after `page.click("#capture-done")`, asserts
`dataset.clicked` is exactly `"true"`. Mutation makes the click write
any other string; equality fails.
