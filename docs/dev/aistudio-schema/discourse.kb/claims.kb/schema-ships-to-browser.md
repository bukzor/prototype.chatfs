---
status: asserted
sources: [sources.kb/readme.md, sources.kb/cdp-capture.md]
depends: [definitions.kb/immutable-js-protos.md]
tags: [aistudio, jspb]
---

Although unavailable from the server, the schema is embedded in the JS that
ships to the browser: the `boq-makersuite` bundle uses Google's immutable JS
protos, whose generated accessors carry field numbers and names.
