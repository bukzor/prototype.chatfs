# Robustness target: handle what the wire format permits

When deciding whether a fragility "needs" a fix, the standard is **"can
the wire format or API contract produce this?"** — not **"has it been
observed to fail in practice?"** Rare-but-permitted edge cases are
required work, not defensive over-engineering.

This calibration runs against the default agent-instinct of
evidence-gated robustness ("haven't seen it fail, so it's not needed").
That instinct produces code that "works until it doesn't" — the failure
arrives once the long-tail input shape finally appears, often in
production.

## Why the stronger target

Two reinforcing reasons:

1. **The wire format is the contract we accepted.** If we accept a
   CDP stream, an HTTP response, a JSON schema, we accepted every
   shape that contract permits. Choosing to handle only the common
   subset is choosing to be silently wrong on the rest.

2. **"Rare" doesn't mean "doesn't happen."** Rare-but-permitted cases
   bite at the worst times — production load, real users, hostile
   environments. Hardening at design time is cheap; hardening after a
   production incident is expensive and reputational.

## Where this applies

Every input boundary:

- **CDP events.** `Network.responseReceived` may arrive without body
  (204, redirect, no-body, loadingFailed, held-drain on shutdown).
  Consumers must tolerate `params.response.body == null`.
- **HTTP responses.** Compressed, chunked, large, slow, partially
  received. Don't assume `Content-Length` is present or correct.
- **JSON schemas.** Optional fields may be `null`, absent, or have
  unexpected nesting. Use null-tolerant readers.
- **Subprocess signals.** SIGPIPE on stdout (downstream `head -n 1`),
  SIGTERM during shutdown, OOM. Handle each documented signal even if
  unobserved.
- **Filesystem entries.** Symlinks, broken symlinks, missing files,
  permission-denied, race-on-rename.

## Calibrating decisions under this target

When evaluating "does this fragility need a fix":

- Read the contract for what it permits.
- If the case is permitted, the fix is needed — regardless of
  observed-failure status.
- If the case is forbidden by the contract, the fix is defensive (and
  may or may not be worth the code cost).

The empirical-evidence question ("has it failed?") is still useful for
*prioritization* — observed failures jump the queue. But it doesn't
move the bar between "needed" and "defensive."

## Origin

User stated this target explicitly 2026-05-12, in the context of the
har-browse tail-latency investigation. Specifically, the chatfs pluckers
were updated to filter bodyless `responseReceived` events even though
the bodyless cases (204/redirect/loadingFailed-with-held) had never
fired for the matching URLs in observed traces. The wire format
permitted bodyless; that was sufficient.
