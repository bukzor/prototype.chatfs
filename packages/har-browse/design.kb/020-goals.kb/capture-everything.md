---
why:
  - data-possession
---

# Capture Everything, Verify Downstream

Record the session's entire network traffic, unfiltered. "All of it"
is a deliberate stand-in for "the data we need": judging relevance at
capture time would require site knowledge the capture stage must not
hold, and a wrong judgment is a silent, usually unrecoverable miss.

Corollaries:

- The capture stage contains zero site knowledge. Understanding what
  the bytes mean is extraction's job (BB2).
- Completeness *verification* is downstream work too: only the
  extractor knows what "the data I need" looks like, so it — not the
  capture — judges whether a capture sufficed and whether to
  recapture.
- The record stays raw enough that a better future extractor can be
  run against old captures without recapture.
