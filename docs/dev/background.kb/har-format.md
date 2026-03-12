# HAR (HTTP Archive) Format

HAR is a JSON-based format for recording HTTP transactions. Playwright and
browser DevTools can produce HAR files capturing all network activity during
a browsing session.

**Relevant properties for chatfs:**

- Contains request/response pairs with headers, bodies, and timing
- Response bodies may be base64-encoded and/or compressed (gzip, brotli)
- A single HAR can contain many entries — extraction must filter by URL pattern
- HAR is the expected artifact format for BB1 (capture)

**Key challenge:** Understanding how Playwright's HAR recording handles content
encodings, streaming responses, and large payloads. This is the primary learning
goal of the playwright-har-capture incubator.
