# Open Architectural Questions

Two hard problems flagged during design but not yet resolved. Both affect
long-term system pleasantness.

## 1. Conversation Identity Across Providers

How to identify "the same conversation" across providers? Each provider uses
its own ID scheme (UUIDs, URLs, opaque strings). If a user discusses the same
topic in Claude and ChatGPT, are those related? Is cross-provider linking
even desirable?

This is the federation problem. Deferred until multi-provider support is
concrete.

## 2. Edit/Fork Storage Without Content Duplication

Forked conversations share a common prefix (all messages before the fork
point). Naively, each fork directory contains its own copy of the shared
prefix. The splat format uses symlinks into a deduplicated `messages/`
directory, solving this for the on-disk case.

For the FUSE layer and cache, the question is whether the VFS should
present deduplicated views (symlinks, hardlinks, or shared backing) or
whether duplication is acceptable given that conversations are small.
