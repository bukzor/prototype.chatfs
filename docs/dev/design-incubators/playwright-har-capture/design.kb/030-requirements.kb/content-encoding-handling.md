---
why:
  - reusable-capture-components
---

# Content Encoding Handling

The toy backend may serve responses with various content encodings (identity,
gzip, brotli). Playwright decompresses HTTP-level encodings before writing the
HAR; the only encoding the plucker must handle is HAR's own base64 wrapper for
binary/non-text content.

**Verification:** The plucker produces identical `extracted.json` regardless of
whether the server used gzip, brotli, or no compression.
