---
why:
  - pipeline-composability
---

# Capnproto Migration

JSONL is the current wire format. If capnshell materializes:

1. Define capnproto schemas for Org, Conversation, Message
2. Swap JSONL serialization for capnproto in pipeline stages
3. Keep JSONL for human debugging
