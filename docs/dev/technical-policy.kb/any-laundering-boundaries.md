---
force: must
source:
  - user review (bukzor), 2026-08-08
  - ../devlog/2026-08-08-001-Pyright-clean-repo-wide--exploration-scripts-typed--not-excluded.md
  - ../devlog/2026-08-08-003-typed-json-extracted-to-GitHub--one-JSON-boundary-repo-wide.md
---

# Any-Laundering Boundaries

Untyped values (`Any` from stdlib or third-party code) enter typed code only
through a **named boundary function** that launders exactly once. Everything
downstream handles honestly-typed values.

## The boundary

- The laundering primitive is `cast`, adjacent to the producing call, with the
  invariant stated. Never an ignore comment (banned repo-wide). Never a
  TypeGuard *at* the boundary: its argument expression is still `Any` at the
  call site, so the diagnostic fires before narrowing can help.
- **One boundary per (program × parser configuration).** A cast asserts "this
  invocation, with these options, yields this shape" — it cannot be shared
  across configurations that guarantee different shapes.
- Cast to the strongest type the producing call guarantees **by construction**:
  - Default-decoder JSON: `typed_json.loads`/`load` (git dependency;
    `github.com/bukzor/typed-json`). Never write a new local JSON alias/cast.
  - Nonstandard decoder: its own boundary module, one cast, config-specific
    alias (e.g. `bukzor.chatgpt_export.json` — `parse_float=Decimal`, so its
    `JsonValue` contains `Decimal` and no `float`).
  - No guarantee at all: `cast(object, ...)` — zero trust; callers narrow.

## Downstream of the boundary

Narrow with `assert isinstance(x, T), x` or a TypeGuard/TypeIs that checks
exactly what it claims. Two anti-patterns:

- A shallow guard claiming a recursive type it didn't walk — a cast in a
  verification costume, worse than an overt cast.
- A deep runtime walk re-proving what the parser guarantees by construction —
  O(n) per load for a tautology. (Deep guards like `typed_json.is_json_value`
  are for values of genuinely *unknown* origin, where no construction
  guarantee exists.)

## Audit

```sh
grep -rn 'cast(' --include='*.py' packages/ docs/
```

Every hit must be a sanctioned boundary or carry its invariant in an adjacent
comment/docstring. A hit that is neither is a policy violation, not a style
choice.
