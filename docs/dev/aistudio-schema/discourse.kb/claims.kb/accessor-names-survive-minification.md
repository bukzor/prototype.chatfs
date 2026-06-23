---
status: asserted
sources: [sources.kb/readme.md]
depends: [definitions.kb/accessor.md]
tags: [jspb, schema]
---

Accessor **method names** (`getTitle`, `getPrompt`, `getRole`) survive
minification, so each recovered field number can be paired with a
human-meaningful field name.
