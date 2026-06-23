---
term: "accessor"
domain: "Google protobuf / closure"
broader: definitions.kb/immutable-js-protos.md
tags: [protobuf, jspb]
---

A generated getter method on an immutable JS proto, of the shape:

    get<Name>(){return _.<prim>(this, [<Ctor>,] <number> [, ...])}

- `<Name>` — survives minification, names the field (`getTitle`, `getRole`).
- `<prim>` — the accessor primitive, encoding the field type.
- `<number>` — the lone integer argument; the proto field number.
- `<Ctor>` — when present, the minified submessage constructor; the edge to
  the next message in the graph.
