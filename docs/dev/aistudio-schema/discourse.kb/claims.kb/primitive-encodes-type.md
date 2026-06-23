---
status: asserted
sources: [sources.kb/readme.md]
depends: [definitions.kb/accessor.md]
tags: [jspb, schema]
---

The accessor primitive (`_.l`, `_.X`, `_.xi`, …) encodes the field's type and
cardinality, and — for submessage fields — carries the constructor of the
nested message as a second argument, forming the edge to the next message in
the graph.
