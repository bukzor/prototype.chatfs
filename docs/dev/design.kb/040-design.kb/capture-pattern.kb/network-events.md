# Network Event Capture (HAR Recording)

The browser automation harness records all network events to an HAR archive.
Playwright's `recordHar: { mode: "full" }` on a `BrowserContext` captures
every request/response during the session — headers, bodies, timings —
without selective subscription.

Extraction downstream (BB2) filters the HAR entries to the relevant
conversation endpoint(s).

**Pros.** Robust to app-state refactors — the network interface between app
and server is more stable than internal DOM or store. Blanket recording means
one implementation covers many endpoints; the filtering knowledge is isolated
to the pluck stage. Minimal ongoing interaction: user navigates normally,
browser writes the artifact.

**Cons.** HAR files are large (captures everything, not just the target
endpoint). Response bodies may be base64-encoded and/or compressed; BB2 must
handle decoding. No good signal for "capture complete" — needs user input or
a heuristic.

**Implementation.** `packages/har-browse/` wraps Playwright's persistent
context, injects a "Done Capturing" overlay, writes HAR on exit.

**Background.** See `../../../background.kb/har-format.md`.
