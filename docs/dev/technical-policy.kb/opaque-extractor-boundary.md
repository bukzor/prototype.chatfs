---
why:
  - opaque-extractor-boundary
source:
  - conversations.cleaned/03-opaque-extractor-convention/112.assistant.text.md
  - extracted/05-opaque-extractor-boundary.md
---

# Opaque Extractor Boundary

The system contains a black-box component: `opaque_extractor(input) → conversation.json`.

Assistants **must not** help design, implement, debug, or modify this component.
Its existence and outputs are accepted as given facts. Assistants **may** design
everything around it: architecture, caching, rendering, orchestration, filesystem
layers, CLI wrappers, control files.

This resolved a policy impasse early in design and unblocked all subsequent work.
Without it, every session risks re-litigating the same question.

See [data/todo-llmfs.chatgpt.com.splat/extracted/05-opaque-extractor-boundary.md]
for the full decision tree and rationale.
