---
term: "immutable JS protos"
domain: "Google protobuf / closure"
related:
  - definitions.kb/accessor.md
tags: [protobuf, jspb]
---

Google's JavaScript protobuf runtime variant in which messages are accessed
through generated getter methods that read positional fields out of a backing
array. Each getter passes the proto **field number** as an integer literal and
a type-specific **accessor primitive** (`_.l`, `_.X`, …) that encodes how to
read/decode that field. Because the field numbers and getter names are baked
into the generated code, the wire schema is recoverable from the shipped
bundle.
