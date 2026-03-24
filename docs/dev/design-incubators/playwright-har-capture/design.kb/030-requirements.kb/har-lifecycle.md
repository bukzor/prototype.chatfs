---
why:
  - reusable-capture-components
---

# HAR Recording Lifecycle

The capture script must demonstrate control over the full HAR lifecycle:

1. Start HAR recording before any navigation
2. Navigate to the target page
3. Inject a control into the page and trigger additional network activity
4. Wait for network idle / specific request completion
5. Finalize and flush the HAR to disk
6. Exit cleanly (nonzero on failure)

**Verification:** The output `.har` file is valid JSON, contains entries for all
expected endpoints, and is not truncated.
