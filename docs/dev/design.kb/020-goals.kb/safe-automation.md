---
why:
  - chatfs
background:
  - policy-safe-automation-boundary
---

# Safe Automation Boundary

The capture step must be human-driven. chatfs must not automate interaction
with provider services — no background scraping, no token extraction, no
request replay. The system works as long as manual web access works; it
doesn't depend on reverse-engineering APIs or evading bot detection.

This makes the architecture durable across provider changes and keeps the
project on the right side of terms of service.
