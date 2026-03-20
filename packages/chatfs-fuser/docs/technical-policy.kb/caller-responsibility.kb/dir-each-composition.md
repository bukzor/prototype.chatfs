---
why:
  - stateless-re-evaluation
source:
  - design-session (2026-03-20)
---

# dir_each Composition

The framework does not provide a `dir_each(list_fn, template_fn)` primitive.
Callers who need the list+template pattern compose it in their `Dir` callback:

```rust
.dir("orgs", move || {
    list_orgs().into_iter().map(|org| {
        (org.clone(), make_org_subtree(&org))
    }).collect()
})
```

This is ordinary Rust composition, not a framework concern.
