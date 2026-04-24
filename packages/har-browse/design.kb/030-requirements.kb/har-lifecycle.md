---
why:
  - reusable-capture-components
---

# Capture Lifecycle

The capture script must demonstrate control over the full capture lifecycle:

1. Attach a CDP session to the browser context before any navigation
2. Enable the `Network` and `Page` CDP domains
3. Navigate to the target page
4. Inject a persistent "Done Capturing" overlay that survives page navigations
5. Human interacts freely (login, 2FA, navigate, scroll)
6. Human clicks "Done Capturing" (or closes the window) to signal completion
7. Drain in-flight body fetches so the final `Network.responseReceived`
   events carry bodies
8. Close the context and exit cleanly (nonzero on failure)

**Verification:** The output JSONL stream is well-formed (one JSON object
per line), contains `Network.responseReceived` events for all expected
endpoints, and those events carry `params.response.body` where the response
had a body. A downstream `chrome-har` pass produces a valid HAR document.
