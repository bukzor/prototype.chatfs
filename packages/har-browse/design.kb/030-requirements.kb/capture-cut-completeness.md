---
why:
  - capture-everything
---

# Capture Cut Completeness

The "Done Capturing" click (or window close) defines a **cut** — a moment
that partitions the capture session. The **cohort** is every network
event that occurred before the cut.

## Requirements

1. **Coverage spans the whole session.** Observation is in place before
   the initial navigation request, and every context the session opens
   (popups, workers, out-of-process frames) is observed from its own
   first request. An attach-time blind window is a completeness bug even
   when no loss is proven (see the gap taxonomy's "requested, never
   seen" class in `../040-design.kb/capture-cut-model.md`).
2. **Every cohort event reaches the output** before the event stream ends.
   This includes events held in internal buffers at cut time (e.g. a
   `responseReceived` stashed awaiting its body) and events still in
   transit from the browser to the capture process.
3. **No silent truncation.** A cohort request that had no terminal event
   (`loadingFinished`/`loadingFailed`) before the cut must still end with
   an explicit terminal record in the output — an abort/cancel event is
   correct; absence is a bug. "This request was cut off by capture
   shutdown" must be distinguishable from "this response had no body."
4. **Shutdown is bounded and event-driven.** The drain completes when the
   cohort's terminal events have all been delivered — a condition detected
   by events, not by waiting a fixed duration. Timers may exist only as
   liveness watchdogs whose firing indicates a defect (and should be loud).

## Non-requirements (explicitly permitted)

- **Response data arriving after the cut need not be captured.** The
  capture may abort in-flight requests at the cut to force prompt,
  evented termination.
- **Requests initiated after the cut may be perturbed or aborted.** Their
  events may still appear in the output (an honest record of the cut) but
  carry no completeness guarantee.

## Why events-before-the-cut is the right cohort

The human clicks Done *after seeing* what they came to capture. Anything
that affected client JS before the click had, by causality, already
arrived over the network before the click. A response still in flight at
cut time is one nobody — neither the human nor client JS — has seen. The
invariant is *what you saw when you clicked is what you get*; it needs no
patience for post-cut arrivals.

Corollary: cut-detection latency (overlay click → capture process notices)
only moves the cut *later*, enlarging the cohort. Detection jitter can
never drop a witnessed event.

**Verification:** For any response rendered by the page before the click,
the output contains its `requestWillBeSent` and `responseReceived` (with
body where one was delivered). For any cohort request unfinished at the
cut, the output contains an explicit terminal event. The stream ends
promptly after the last cohort event — not after a fixed timeout — and a
capture containing a hung or held-open request (e.g. an EventSource)
still terminates.
