---
why:
  - chatfs
---

# Unix Tool Composability

The pipeline stages and filesystem output should work with standard Unix
tools — jq, grep, find, cat, pipes. No special client required.

Each stage is a standalone CLI tool with file or stdin/stdout interfaces.
The system is composable: you can use any stage independently, or pipe them
together.
