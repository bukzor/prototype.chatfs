# Capture Patterns

Browser-side mechanisms for producing the BB1 capture artifact. Each file
describes one mechanism for getting conversation data out of the provider's
web app.

## What belongs here

- A specific browser-side capture mechanism (injected UI, network recording,
  CDP session, wizard-assisted manual capture, etc.)
- What the mechanism observes (page state, DOM, network events)
- How the payload is handed to the daemon
- Tradeoffs (UX cleanliness, policy safety, robustness to app changes)

## What does NOT belong

- Which pattern is currently chosen — see `../capture-pattern.md`
- Provider-specific extraction logic (opaque extractor boundary)
- Post-capture processing — see `../black-box-decomposition.md` (BB2, BB3)

## When to add

New capture mechanisms worth considering (or that were considered and rejected
with durable reasoning) get their own file here. Transient variants don't.
