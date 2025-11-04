# Design Rationale

**Last Updated:** 2025-11-01

**Read this when:**

- Questioning why a design decision was made
- Considering changing a core architectural choice
- Onboarding new contributors who ask "why?"

This document explains the reasoning behind major architectural decisions for
chatfs.

## The Problem

Your conversations on claude.ai (and ChatGPT, Gemini) are trapped in web UIs. You can't:

- **grep** across conversation history
- **pipe** conversations to other tools (analysis, LLMs, scripts)
- **use them as data** sources for automation
- **work offline** using standard tools

The data is locked in browser tabs, inaccessible to the Unix toolchain.

**Why existing solutions don't work:**

- **Official Anthropic API:** Cannot access claude.ai conversations (separate systems - the API creates new chats, doesn't read existing ones)
- **Browser extensions:** Manual one-shot exports, no incremental updates, no CLI access
- **Copy-paste:** Doesn't scale, loses metadata, breaks on updates

**What's needed:** Conversations as files in a filesystem, with lazy loading and standard tool compatibility.

chatfs solves this by treating chat history as a lazily-loaded filesystem using composable JSONL layer tools.

## Core Decisions

### Layered Architecture (Four Layers)

**Decision:** Build as four-layer architecture: native → vfs → cache → cli

**Layers:**

- **M1-CLAUDE (native):** Direct API wrapper, outputs raw provider data as JSONL
- **M2-VFS (normalized):** Provider-agnostic JSONL schema across providers
- **M3-CACHE (persistence):** Filesystem storage with staleness tracking
- **M4-CLI (UX):** Human-friendly commands with colors, progress bars

**Alternatives Considered:**

- **Option A: Monolithic CLI** (like `chatfs ls`, `chatfs cat` with subcommands)

  - Pros: Faster to initial MVP, familiar Git-like UX, easier state management
  - Cons: Harder to compose with other tools, requires refactor for capnshell,
    doesn't inform future tool design

- **Option B: Composable JSONL layers** (separate programs at each abstraction level)
  - Pros: Works with jq/Unix tools immediately, cheap capnshell adapter, natural
    integration with future AI tools, learn-then-abstract approach
  - Cons: More programs to write, IPC overhead (minor)

**Rationale:** Chose Option B (evolved to 4 layers) because:

1. **Useful immediately** - Composes with existing Unix tools (jq, grep, etc.)
2. **Cheap capnshell migration** - Just swap serialization format (JSONL →
   capnproto)
3. **Informs future design** - Learn which compositions matter before building
   capnshell
4. **Natural AI integration** - Pipe conversations to future coding assistant
   (aider-ng)
5. **Aligns with project philosophy** - "DIY/composable" tools

**Tradeoffs:**

- **Gave up:** Speed to MVP (more programs to write)
- **Gained:** Flexibility, composition, learning, future-proofing

**Impact:** Affects all tool design, testing strategy, documentation structure

**Evolution:** Originally designed as plumbing/porcelain split (2 layers), evolved to 4 layers to support learn-then-abstract approach (build M1-CLAUDE before designing M2-VFS normalization).

See [layered-architecture] for detailed analysis.

### JSONL for Data Interchange

**Decision:** Use JSONL (JSON Lines) for stdin/stdout between JSONL layers (M1-CLAUDE, M2-VFS, M3-CACHE)

**Alternatives Considered:**

- **Option A: Plain JSON**

  - Pros: Well-known, human-readable
  - Cons: Not streaming-friendly (need to parse entire structure), harder to
    pipe

- **Option B: JSONL**

  - Pros: Streaming (process line-by-line), works with jq, easy testing (echo
    one line), future capnproto migration is just serialization swap
  - Cons: Slightly less human-readable than pretty-printed JSON

- **Option C: Capnproto immediately**
  - Pros: Efficient binary format, schema validation, future-proof
  - Cons: Requires capnshell to be useful, can't use with existing Unix tools,
    premature optimization

**Rationale:** Chose Option B because:

1. **Streaming** - Process conversations as messages arrive (one JSON object per
   line)
2. **Unix composability** - Works with jq, grep, head, tail now
3. **Simple testing** - `echo '{"test":"data"}' | tool | jq`
4. **Easy migration path** - When capnshell exists, swap JSONL → capnproto in
   JSONL layer tools (M1-CLAUDE, M2-VFS, M3-CACHE)
5. **Deferred commitment** - Don't need capnshell working to make progress

**Tradeoffs:**

- **Gave up:** Slight efficiency (text vs binary), type safety (no schema
  validation yet)
- **Gained:** Works today with existing tools, incremental migration path

**Impact:** All JSONL layer I/O (M1-CLAUDE, M2-VFS, M3-CACHE), testing strategy, future capnshell
integration

### Lazy Filesystem Model

**Decision:** Create files/directories on-demand, track staleness via mtime

**Alternatives Considered:**

- **Option A: Eager sync** (fetch all conversations upfront)

  - Pros: Simple implementation, always have data
  - Cons: Slow startup (users have 100s-1000s of conversations), wastes
    bandwidth, most conversations never accessed

- **Option B: Lazy creation with mtime tracking via explicit CLI calls**

  - Pros: Fast (only fetch when accessed via CLI), efficient (cache staleness via
    filesystem), scales to any conversation count, FUSE-compatible design (clear correlation between CLI commands and potential FUSE callbacks)
  - Cons: More complex logic, empty stub files, requires staleness checks

- **Option C: Virtual filesystem (FUSE)**
  - Pros: No real files (truly on-demand), automatic staleness
  - Cons: Requires root/FUSE kernel module, breaks offline access, complex
    implementation

**Rationale:** Chose Option B because:

1. **Scales** - Works for 10 conversations or 10,000
2. **Fast** - Only pay for what you use (explicit CLI calls, not syscalls)
3. **Offline-friendly** - Files persist, work with cat/grep when offline
4. **Simple staleness** - Filesystem mtime = conversation.updated_at
5. **No special dependencies** - Just Python + files
6. **FUSE-compatible** - Design maintains clear correlation between CLI commands and potential FUSE callbacks (secondary requirement)

**Tradeoffs:**

- **Gave up:** Simplicity (empty stubs, staleness logic), slight disk usage
  (metadata files)
- **Gained:** Performance, scalability, offline access, no FUSE dependency

**Impact:** Cache implementation, user experience, performance characteristics

See [lazy-filesystem] for detailed analysis.

### Unofficial API Instead of Official

**Decision:** Use unofficial claude.ai API (st1vms) instead of official
Anthropic API

**Alternatives Considered:**

- **Option A: Official Anthropic API** (https://api.anthropic.com)

  - Pros: Reliable, documented, production-ready, cheap ($3/$15 per million
    tokens)
  - Cons: **Cannot access claude.ai conversations** (separate systems),
    stateless, no browsing/export of existing chats

- **Option B: Unofficial claude.ai API** (st1vms/unofficial-claude-api)
  - Pros: **Accesses claude.ai conversations**, works now, serves our niche
    (conversation access), proven stable (three years in practice)
  - Cons: Unmaintained, could break, requires session key, uses curl_cffi for
    Cloudflare bypass

**Rationale:** Chose Option B because:

1. **Solves the problem** - Official API **cannot access claude.ai
   conversations**
2. **Only working option** - Uses curl_cffi to bypass Cloudflare TLS
   fingerprinting
3. **Serves our niche** - We need conversation access, not chatbot building
4. **Acceptable risk** - Unmaintained but stable (three years of observed stability; internal APIs appear notably stable)

**Tradeoffs:**

- **Gave up:** Reliability guarantees, official support
- **Gained:** Actual access to claude.ai conversations (the entire point)

**Impact:** Core functionality, maintenance burden, auth requirements

See [unofficial-api] for ecosystem history and alternatives.

### Documentation-First Approach

**Decision:** Build comprehensive documentation before implementing code

**Alternatives Considered:**

- **Option A: Code first, document later**

  - Pros: Faster to working prototype, discover issues through implementation
  - Cons: Design decisions implicit, hard to maintain direction across sessions,
    LLM loses context

- **Option B: Document architecture, then implement**
  - Pros: Explicit decisions, multi-session continuity, LLM has clear context,
    easier to change design before code exists
  - Cons: Slower to first working code, possible over-design

**Rationale:** Chose Option B because:

1. **Multi-session project** - Will take weeks/months, documentation maintains
   continuity
2. **LLM collaboration** - Claude needs explicit context across sessions
3. **Design exploration** - Fork representation, M4-CLI UX, capnshell
   integration need thought
4. **Cheaper to change** - Easier to revise docs than refactor code

**Tradeoffs:**

- **Gave up:** Quick prototype dopamine, learning from implementation mistakes
- **Gained:** Clear direction, session continuity, explicit rationale

**Impact:** Project timeline, session workflow, design quality

## Related Documents

- [technical-design.md] - What the system is (implementation of these decisions)
- [development-plan.md] - How we build it (milestones based on these decisions)
- [design-incubators] - Unsolved problems being explored

[layered-architecture]: design-rationale/layered-architecture.md
[lazy-filesystem]: design-rationale/lazy-filesystem.md
[unofficial-api]: design-rationale/unofficial-api.md
[technical-design.md]: technical-design.md
[development-plan.md]: development-plan.md
[design-incubators]: ../../design-incubators/
