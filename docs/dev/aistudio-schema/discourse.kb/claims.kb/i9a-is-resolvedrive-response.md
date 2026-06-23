---
status: asserted
likelihood: 1.0
sources: [sources.kb/readme.md, sources.kb/bundle-audit.md]
tags: [aistudio, graph, entrypoint]
---

The minified constructor `i9a` (in `bundles/_b.js`) is the
`ResolveDriveResource` **response** message — the graph-walk entry point.

**Verified** against the RPC stub at `_b.js:42772`, which lists the method
path, then `_.h9a` (request), then `i9a` (response). No longer inferred from
the README usage comment alone — hence 1.0.
