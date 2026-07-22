---
status: todo
---

# `capture.mjs`: truncation marker omitted from grace-expiry-flushed responses

**Priority:** Medium. **Confidence:** High.

Prospective — targets fix 3 in `packages/har-browse/.claude/todo.kb/
2026-07-22-000-Done-Capturing-race-drops-in-flight-requests-with-no-
drain.md`, not yet implemented. If the expiry flush emits the stashed
`Network.responseReceived` but forgets to set the marker, a truncated
response becomes indistinguishable from a legitimately body-less
complete response (204s, redirects, `getResponseBody` rejections all
emit bare RRs today). Downstream consumers lose the ability to tell
"this response was cut off by capture shutdown" from "this response had
no body" — the grep-able signature fix 3 exists to provide.

## Injection

```diff
   const flush = () => {
     for (const [, rr] of awaitingBody) {
-      rr.response.harBrowseTruncated = true;
       enqueue({ method: "Network.responseReceived", params: rr });
     }
     awaitingBody.clear();
   };
```

## Anticipated Test Coverage

Same fixture as `drain-expiry-flush-removed.md` (headers sent, body held
open past grace). The assertion there already checks
`response.harBrowseTruncated === true` by equality, not mere
RR-presence, so it kills this mutant too — worth confirming one test
covers both rather than duplicating.
