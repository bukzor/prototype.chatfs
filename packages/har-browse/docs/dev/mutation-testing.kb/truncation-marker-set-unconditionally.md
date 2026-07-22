---
status: todo
---

# `capture.mjs`: truncation marker applied to all responses, not just expiry-flushed ones

**Priority:** Medium. **Confidence:** High.

Prospective — targets fix 3 in `packages/har-browse/.claude/todo.kb/
2026-07-22-000-Done-Capturing-race-drops-in-flight-requests-with-no-
drain.md`, not yet implemented. Inverse of
`drain-expiry-flush-marker-dropped.md`: if the marker assignment
migrates into the shared RR-emit path (e.g. into `onLoadingFinished`)
instead of staying confined to the expiry flush, every response in every
capture claims to be truncated. Downstream tooling that filters or warns
on truncated responses would flag everything; the marker becomes noise
and the wire format silently grows a bogus field on the happy path.

## Injection

```diff
 async function onLoadingFinished(lf) {
   const rr = awaitingBody.get(lf.requestId);
   awaitingBody.delete(lf.requestId);
   if (rr) {
     try {
       const body = await session.send("Network.getResponseBody", { requestId: lf.requestId });
       rr.response.body = body.body;
       if (body.base64Encoded) rr.response.encoding = "base64";
     } catch {}
+    rr.response.harBrowseTruncated = true;
     enqueue({ method: "Network.responseReceived", params: rr });
   }
   enqueue({ method: "Network.loadingFinished", params: lf });
 }
```

## Anticipated Test Coverage

Any existing full-event-shape assertion on a completed response should
catch this if it compares the response object by equality (extra key ⇒
inequality). If existing RR assertions are all field-plucking
(`.body`, `.encoding` only), add an explicit
`"harBrowseTruncated" in rr.response === false` check to the
normal-completion path of the fix-3 test. Cheap, deterministic.
