---
why:
  - undisruptive-launch
---

# Undisrupted Operator Input

Launching a capture must not divert keystrokes the operator intends for
another window (chat, terminal, editor) into the not-yet-ready capture
window.

**Verification:** Type continuously into another application spanning
the moment `har-browse` launches its window; none of that input appears
anywhere in the capture window.
