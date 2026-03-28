# chatfs — Filesystem Access to LLM Conversations

LLM chat conversations are trapped in provider web UIs. You can't search them
with grep, browse them in a file manager, back them up, or process them with
Unix tools. Each provider has its own interface, its own export format (if any),
and no interoperability.

chatfs exposes conversations from multiple providers (Claude, ChatGPT, etc.)
as a mounted filesystem. Conversations appear as ordinary files and directories
that standard tools can read, search, and process.

## Who Benefits

Anyone who accumulates significant conversation history across LLM providers
and wants to treat it as data they own — searchable, browsable, archivable,
composable with existing tools.

## What Success Looks Like

```bash
ls /mnt/llmfs/claude.ai/Buck\ Evan/2025-10/
grep -r "FUSE" /mnt/llmfs/
cat /mnt/llmfs/chatgpt/2025-10/architecture-discussion.md
```

Conversations are files. Standard tools work. No provider lock-in.
