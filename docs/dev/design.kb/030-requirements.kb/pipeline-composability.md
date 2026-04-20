---
why:
  - unix-composability
  - multi-provider
---

# Pipeline Composability

The capture-to-rendering pipeline must decompose into independent stages
connected by file I/O. Each stage is a standalone CLI tool that can be run,
tested, and replaced independently. Providers implement their own stages
without affecting the rest.

**Verification:** Replace one stage's implementation (e.g. swap a capture
tool) without modifying any other stage.
