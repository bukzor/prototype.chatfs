---
why:
  - reusable-capture-components
---

# Content Encoding Handling

The toy backend serves responses with multiple content encodings (identity,
gzip, brotli). The capture and extraction pipeline must handle all of them
correctly.

**Verification:** The plucker produces identical `extracted.json` regardless of
whether the server used gzip, brotli, or no compression.
