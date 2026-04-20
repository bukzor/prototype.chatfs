# Inject UI, Read from Page State

`addInitScript` injects a floating "Export" button into the page. On click,
injected JS pulls the conversation from the app's internal state (framework
store, window globals), serializes it, and hands it off.

Payload handoff: use `exposeFunction` to send the payload directly to the
daemon. Avoids the downloads folder and the clipboard — both lossy for
structured data.

**Pros.** Clean UX; uses the app's own parsed representation, so structure
(forks, metadata) survives.

**Cons.** Tightest coupling to the app's internals. Breaks when the store
shape changes.
