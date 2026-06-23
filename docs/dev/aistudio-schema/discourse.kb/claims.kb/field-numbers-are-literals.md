---
status: asserted
sources: [sources.kb/readme.md]
depends: [definitions.kb/accessor.md]
tags: [jspb, schema]
---

In the generated accessors, the proto **field number** appears as an integer
literal — the lone integer argument to the accessor primitive. It is therefore
directly readable out of the minified bundle.
