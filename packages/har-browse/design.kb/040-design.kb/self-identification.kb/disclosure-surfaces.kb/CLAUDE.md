---
why:
  - unblocked-sessions
---

# Disclosure Surfaces

One file per channel that can carry "this is har-browse" to a site.

They are not interchangeable. Each reaches a different set of servers,
and each has a different cost against `unblocked-sessions`' requirement
that the session stay indistinguishable from a real browser in every
other respect. Each file opens with its verdict.

Two are shipped, and they are complementary rather than redundant: the
User-Agent comment reaches servers that read `User-Agent`, the brand
list reaches those that read only client hints. The measurements they
cite are in `../ua-position-gate.md`.

## What belongs here

- A channel we use, could use, or have ruled out — including ruled-out
  ones, so they are not re-proposed.
- Its verdict, what it reaches, what it costs, and what it would take.

## What does NOT belong

- The measurements themselves → `../ua-position-gate.md`.
- Fingerprint surfaces that aren't disclosure (automation tells, TLS,
  `navigator.webdriver`) — those live with the launch flags that set them.

## A note on the choice

None of these makes the session *less* like a real browser in any other
respect. The truthful client-hint metadata, the real platform, the real
Chrome version, and the pinned browser revision are unaffected by which
one we pick — which is the point. Disclosure is additive, not a
substitute for being what we claim to be.
