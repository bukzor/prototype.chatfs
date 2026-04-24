---
why:
  - reusable-capture-components
---

# Content Encoding Handling

The toy backend may serve responses with various content encodings (identity,
gzip, brotli). Chromium decompresses HTTP-level encodings before
`Network.getResponseBody` returns; the only encoding the plucker must
handle is the base64 wrapper Chromium applies (via `base64Encoded: true`)
for non-text MIME types.

**Verification:** The plucker produces identical `extracted.json` regardless
of whether the server used gzip, brotli, or no compression.
