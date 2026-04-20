---
why:
  - chatfs
---

# Multi-Provider Support

chatfs should work across LLM chat providers — Claude (claude.ai), ChatGPT
(chat.openai.com), Google AI Studio (aistudio.google.com), and others. The
user's conversation history is scattered; chatfs unifies access.

Adding a new provider should not require changes to the core system. The
filesystem, cache, and rendering layers are provider-agnostic; only the
capture and extraction stages are provider-specific.
