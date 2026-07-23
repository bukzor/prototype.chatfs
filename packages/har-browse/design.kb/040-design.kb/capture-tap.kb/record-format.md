---
why:
  - capture-everything
  - crash-durability
  - capture-cut-completeness
  - cli-interface
---

# Record Format: Streamed JSONL of CDP Events

One JSON object per line on stdout, in CDP wire shape `{method,
params}`, emitted as events occur. Streaming — not batching at capture
end — is what makes crash-durability hold. Response bodies are attached
at `Network.responseReceived.params.response.body`, with
`params.response.encoding = "base64"` exactly when the body is a
base64-wrapped binary payload.

The CDP shape is a convenience of the chosen tap point, not a
commitment inherited from the requirements layer: it is what the tap
emits natively, and `chrome-har`'s `harFromMessages` turns it into a
bonafide HAR unmodified. A different tap point would induce a
different record shape; consumers needing long-term format stability
should derive HAR rather than depend on the raw stream shape.
