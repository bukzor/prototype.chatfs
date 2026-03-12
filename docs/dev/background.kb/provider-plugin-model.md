# Provider Plugin Model

chatfs is provider-agnostic. Each chat service (Claude, ChatGPT, Gemini, etc.)
is a provider module implementing a common interface over the black boxes plus
cache layout rules.

**A provider defines:**

1. How to parse a `ConversationRef` (URL, ID, "active tab")
2. Where artifacts and outputs live in the cache
3. How to invoke BB1 (capture), BB2 (extract), BB3 (emit)
4. How to detect staleness (manual-only, TTL, version file)
5. What the mounted directory structure looks like

**Mount layout:** Providers mount under `/mnt/llmfs/<provider>/` (e.g.,
`chatgpt/`, `claude.ai/`). The filesystem core never needs to know message
schemas — only that the provider can materialize a conversation into cache
when asked.

**Provider manifest** (per-provider configuration):
- Accepted `conv_ref` forms (URL, ID, "active tab")
- Artifact landing paths
- Cache locations
- TTL/invalidation rules (manual-only, time-based, version file)
- How to report "needs user interaction" (for wizard-style capture)

**Current state:** `native/claude` exists as a Python JSONL layer. Future
providers (`native/chatgpt`, `native/gemini`) follow the same pattern.
