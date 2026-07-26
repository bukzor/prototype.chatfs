# Devlog: 2026-07-23 — har-browse Done-button invisible on aistudio.google.com (Trusted Types)

## Focus

User-filed bug: the injected `#capture-done` overlay works on chatgpt.com
and claude.ai but never appears on aistudio.google.com. Live debugging
found the element completely absent from the DOM (not just hidden),
while the injected `<style>` tag was present.

## Decisions

### Trusted Types pass-through policy, not imperative DOM rebuild

**Root cause:** aistudio.google.com serves `Content-Security-Policy:
require-trusted-types-for 'script'` (confirmed via response headers).
That rejects a raw-string `insertAdjacentHTML`; the call in `inject()`
(`src/inject.mjs`) threw and silently aborted the rest of injection.
The `<style>` tag lands first via `.textContent` (not a guarded sink),
which is why CSS survived but the HTML never did.

**Rationale:** Wrapped the fixed, locally-authored overlay markup in a
feature-detected `window.trustedTypes.createPolicy(...)` pass-through
policy before the `insertAdjacentHTML` call — smallest possible diff,
no-op on sites without Trusted Types enforcement.

**Alternatives considered:** Rewriting `inject()` to build the overlay
via imperative `createElement`/`appendChild` calls (avoids Trusted
Types entirely, more future-proof against a stricter `trusted-types`
allowlist directive) — rejected as unnecessary churn until/unless that
directive actually shows up.

### Cast `window.trustedTypes` narrowly instead of adding ambient types

**Rationale:** `@types/trusted-types` isn't in the dependency tree and
this is the only touch-point; a local `/** @type {any} */` cast at the
call site was cheaper than tsconfig/dependency changes for one API.

## Conventions Established

- When a page-injected script partially fails, check whether earlier
  statements in the same function used a different (non-Trusted-Types-guarded)
  DOM API than later ones — the split between what landed and what
  didn't localizes the throwing line without needing console access.

## Open Questions

- Live validation against the real aistudio.google.com is done (user
  confirmed the button now appears); no open questions remain.

## References

- `packages/har-browse/src/inject.mjs`
- `packages/har-browse/tests/persistent_injection.spec.mjs` (new
  "Trusted Types CSP" regression test)
- `packages/har-browse/tests/_common/server.mjs` (`/trusted-types` route)
- `packages/har-browse/.claude/todo.md`
