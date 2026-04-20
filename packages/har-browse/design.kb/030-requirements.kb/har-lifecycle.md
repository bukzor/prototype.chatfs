---
why:
  - reusable-capture-components
---

# HAR Recording Lifecycle

The capture script must demonstrate control over the full HAR lifecycle:

1. Start HAR recording before any navigation
2. Navigate to the target page
3. Inject a persistent "Done Capturing" overlay that survives page navigations
4. Human interacts freely (login, 2FA, navigate, scroll)
5. Human clicks "Done Capturing" to signal completion
6. Finalize and flush the HAR to disk
7. Exit cleanly (nonzero on failure)

**Verification:** The output `.har` file is valid JSON, contains entries for all
expected endpoints, and is not truncated.
