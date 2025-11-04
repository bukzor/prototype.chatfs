# Technical Design

**Last Updated:** 2025-11-01

**Status:** ⚠️ Pre-implementation - Technical details are soft and under
discussion. Data structures, APIs, and implementation specifics will be refined
during Milestone 1.

**Read this when:**

- Understanding the three-layer architecture (API/Cache/CLI)
- Implementing M1 API layer tools
- Understanding data flow and component interactions
- Planning M2/M3 implementation
- Onboarding as a contributor

This document describes chatfs's architecture and milestone-based implementation plan.

## System Overview

chatfs provides programmatic access to claude.ai conversations through composable JSONL-based tools, built in three layers (API, Cache/FS, CLI).

**Current state (M1):**
- Stateless API layer tools (`chatfs-api-*`)
- No caching, no filesystem writes
- Pure JSONL pipelines composing with Unix tools

**Future layers:**
- **M2:** Cache/FS layer adds persistence, staleness checking, lazy loading
- **M3:** CLI layer adds human-friendly UX with colors and progress bars

**Design characteristics:**

- **Composable:** Small tools that pipe together (Unix philosophy)
- **Layered:** Three independent layers (API/Cache/CLI) with clear boundaries
- **Progressive:** Each layer builds on the previous, each independently useful
- **Future-proof:** JSONL → capnproto migration path
- **Multi-provider ready:** Design supports ChatGPT, Gemini via provider abstraction

## Architecture

chatfs is built in three layers, each implemented in separate milestones:

```
┌─────────────────────────────────────────┐
│      CLI Layer (M3 - Future)            │
│   chatfs ls "Buck Evan/2025-10-29"      │
│   chatfs cat "path/to/conversation.md"  │
│   Commands: chatfs-*                    │
│   Modules: chatfs.layer.cli.*           │
└─────────────────┬───────────────────────┘
                  │ Uses
┌─────────────────▼───────────────────────┐
│    Cache/FS Layer (M2 - Future)         │
│   chatfs-cache-list-orgs                │
│   chatfs-cache-list-convos              │
│   chatfs-cache-get-convo                │
│   Commands: chatfs-cache-*              │
│   Modules: chatfs.layer.cache.*         │
└─────────────────┬───────────────────────┘
                  │ Uses
┌─────────────────▼───────────────────────┐
│       API Layer (M1 - Current)          │
│   chatfs-api-list-orgs                  │
│   chatfs-api-list-convos                │
│   chatfs-api-get-convo                  │
│   chatfs-api-render-md                  │
│   Commands: chatfs-api-*                │
│   Modules: chatfs.layer.api.*           │
└─────────────────┬───────────────────────┘
                  │ Uses
┌─────────────────▼───────────────────────┐
│        Shared Libraries                 │
│  chatfs.client   (API wrapper)          │
│  chatfs.models   (Data structures)      │
└─────────────────┬───────────────────────┘
                  │ Uses
┌─────────────────▼───────────────────────┐
│    unofficial-claude-api (Vendored)     │
│    st1vms Python client                 │
└─────────────────┬───────────────────────┘
                  │ HTTP/TLS
┌─────────────────▼───────────────────────┐
│         claude.ai API                   │
└─────────────────────────────────────────┘
```

**Layer responsibilities:**

- **API Layer (M1):** Stateless JSONL tools, pure API calls, no filesystem interaction
- **Cache/FS Layer (M2):** Filesystem persistence, staleness checking, lazy loading
- **CLI Layer (M3):** Human-friendly commands, colors, progress bars, interactive features

**Why three layers?**
- Each layer independently useful (can use API layer directly with jq)
- Clear milestone boundaries (M1→M2→M3)
- Allows users to choose abstraction level based on needs

## Components

### API Layer (M1 - Current)

**Milestone:** M1
**Commands:** `chatfs-api-*`
**Modules:** `chatfs.layer.api.*`

**Responsibility:** Stateless JSONL tools that call claude.ai API directly. No caching, no filesystem writes.

**Interface:**

```bash
# Read JSONL from stdin, write JSONL to stdout
echo '{"uuid":"org-123"}' | chatfs-api-list-convos | jq
```

**Tools:**

**chatfs-api-list-orgs** (`chatfs.layer.api.list_orgs`)

- Input: None required (can accept `{}` empty object on stdin, but ignores it; starting point for pipelines)
- Output: One JSON object per org per line
- Schema: `{uuid, name, created_at, ...}`
- Behavior: Calls API every time (no caching)

**chatfs-api-list-convos** (`chatfs.layer.api.list_convos`)

- Input: Org record `{uuid, ...}`
- Output: One JSON object per conversation per line
- Schema: `{uuid, title, created_at, updated_at, org_uuid, ...}`
- Behavior: Calls API every time (no caching)

**chatfs-api-get-convo** (`chatfs.layer.api.get_convo`)

- Input: Conversation record `{uuid, ...}`
- Output: One JSON object per message per line
- Schema: `{type: "human"|"assistant", text, created_at, ...}`
- Behavior: Calls API every time (no caching)

**chatfs-api-render-md** (`chatfs.layer.api.render_md`)

- Input: Message records (JSONL)
- Output: Markdown with YAML frontmatter (NOT JSONL)
- Format: See [markdown-format]
- Behavior: Pure transformation, no API calls

**Contract:**
- Read JSONL from stdin (except list-orgs)
- Write JSONL to stdout (except render-md → markdown)
- Log errors to stderr
- Exit 0 on success
- No terminal dependencies (no colors, progress bars)
- No filesystem interaction (stateless)

### Shared Libraries (M1)

**chatfs.client** - API Client Wrapper

**Responsibility:** Wrap unofficial-claude-api, handle auth, normalize responses

**Interface:**

```python
from chatfs.client import Client

client = Client()  # Uses CLAUDE_SESSION_KEY from env
orgs = client.list_organizations()
convos = client.list_conversations(org_uuid="...")
messages = client.get_conversation(convo_uuid="...")
```

**Key methods:**

- `list_organizations() → List[Org]`
- `list_conversations(org_uuid: str) → List[Conversation]`
- `get_conversation(convo_uuid: str) → List[Message]`

See [provider-interface] for full API documentation.

**chatfs.models** - Data Structures

**Responsibility:** Type definitions for org, conversation, message

**Structures:**

```python
@dataclass
class Org:
    uuid: str
    name: str
    created_at: datetime

@dataclass
class Conversation:
    uuid: str
    title: str
    created_at: datetime
    updated_at: datetime
    org_uuid: str

@dataclass
class Message:
    type: Literal["human", "assistant"]
    text: str
    created_at: datetime
    uuid: str
```

### Cache/FS Layer (M2 - Future)

**Milestone:** M2
**Commands:** `chatfs-cache-*`
**Modules:** `chatfs.layer.cache.*`

**Responsibility:** Filesystem persistence, staleness checking, lazy directory creation

**Examples:**

```bash
# Same interface as API layer, but with caching
chatfs-cache-list-orgs | jq
chatfs-cache-list-convos | jq
chatfs-cache-get-convo | chatfs-api-render-md > conversation.md
```

**Implementation:** Wraps API layer tools, adds:

- Filesystem writes to `./chatfs/` directory structure
- Staleness checking via mtime comparison
- Lazy directory/file creation
- Cache invalidation based on `updated_at` fields

**Shared library:**

**chatfs.cache** - Filesystem Cache Manager

```python
from chatfs.cache import Cache

cache = Cache(base_path="./chatfs")
cache.ensure_org_dir(org_name="Buck Evan")
cache.write_conversation(path="...", messages=[...])
cache.is_stale(path="...", remote_updated_at="...")
```

See [cache-layer] for staleness logic and directory structure.

### CLI Layer (M3 - Future)

**Milestone:** M3
**Commands:** `chatfs-*` (no prefix)
**Modules:** `chatfs.layer.cli.*`

**Responsibility:** Human-friendly CLI wrappers with rich UX

**Examples:**

```bash
chatfs ls "Buck Evan"               # List conversations
chatfs cat "path/to/convo.md"       # Read conversation
chatfs sync "Buck Evan/2025-10"     # Force refresh
```

**Implementation:** Wraps Cache layer tools, adds:

- Path parsing (org name → org UUID lookup)
- Progress bars for slow operations
- Colors/formatting for terminal output
- Friendly error messages
- Interactive prompts

See [porcelain-layer] for UX design.

## Data Flow

### M1: API Layer (Stateless)

**List Organizations**

```
chatfs-api-list-orgs
  ↓
chatfs.client.Client.list_organizations()
  ↓
unofficial-claude-api HTTP request
  ↓
claude.ai API response
  ↓
chatfs.models.Org objects
  ↓
Serialize to JSONL stdout
  ↓
Output: {"uuid": "...", "name": "Buck Evan", ...}
```

**List Conversations for Org**

```
echo '{"uuid":"org-123"}' | chatfs-api-list-convos
  ↓
Parse JSONL stdin → org_uuid
  ↓
chatfs.client.Client.list_conversations(org_uuid)
  ↓
unofficial-claude-api HTTP request
  ↓
claude.ai API response
  ↓
chatfs.models.Conversation objects
  ↓
Serialize to JSONL stdout
  ↓
Output: {"uuid": "...", "title": "...", "created_at": "...", ...}
```

**Get Conversation Messages**

```
echo '{"uuid":"convo-456"}' | chatfs-api-get-convo
  ↓
Parse JSONL stdin → convo_uuid
  ↓
chatfs.client.Client.get_conversation(convo_uuid)
  ↓
unofficial-claude-api HTTP request
  ↓
claude.ai API response
  ↓
chatfs.models.Message objects
  ↓
Serialize to JSONL stdout
  ↓
Output: {"type": "human", "text": "...", ...}
        {"type": "assistant", "text": "...", ...}
```

**Render to Markdown**

```
chatfs-api-get-convo | chatfs-api-render-md
  ↓
Parse JSONL stdin → List[Message]
  ↓
Generate YAML frontmatter (uuid, created_at, updated_at, etc.)
  ↓
Format messages as markdown sections
  ↓
Markdown output (NOT JSONL):
---
uuid: ...
created_at: ...
---

**Human:** Question here

**Claude:** Answer here
```

### M2: Cache/FS Layer (With Persistence)

**List Organizations (Cached)**

```
chatfs-cache-list-orgs
  ↓
chatfs.cache.Cache.is_stale("./chatfs/orgs.jsonl")
  ↓ (if stale or missing)
Call: chatfs-api-list-orgs (subprocess)
  ↓
Parse output, write to ./chatfs/orgs.jsonl
  ↓
Set mtime to current time
  ↓
Output cached JSONL
```

Similar pattern for `chatfs-cache-list-convos` and `chatfs-cache-get-convo`: check cache, call API layer if stale, write to filesystem, output JSONL.

## Data Structures

### JSONL Format

**One JSON object per line:**

```jsonl
{"uuid":"123","name":"Buck Evan","created_at":"2025-10-15T10:00:00Z"}
{"uuid":"456","name":"Another Org","created_at":"2025-10-20T12:00:00Z"}
```

**Properties:**

- UTF-8 encoding
- Newline-separated (one object per line)
- No trailing commas
- Each line is valid JSON on its own
- Streamable (process line-by-line)

### Org Record

```json
{
  "uuid": "6e56e06e-6669-4537-a77c-ae62b3d3c221",
  "name": "Buck Evan",
  "created_at": "2025-10-15T10:00:00Z"
}
```

### Conversation Record

```json
{
  "uuid": "7ddc2006-e624-4fb6-ba88-b642827a2606",
  "title": "Tshark HTTP request filtering",
  "created_at": "2025-10-29T13:33:33Z",
  "updated_at": "2025-10-29T13:33:42Z",
  "org_uuid": "6e56e06e-6669-4537-a77c-ae62b3d3c221",
  "message_count": 4
}
```

### Message Record

```json
{
  "type": "human",
  "text": "How do I filter tshark to show only HTTP requests?",
  "created_at": "2025-10-29T13:33:33Z",
  "uuid": "msg-123"
}
```

## Filesystem Cache Structure (M2 - Future)

**Milestone:** M2 (not implemented in M1)

The Cache/FS layer will introduce persistent filesystem storage:

```
./chatfs/
├── .config.json                    # Session key, default org
└── claude.ai/
    └── Buck Evan/                  # Organization name
        ├── org.jsonl               # Org metadata
        ├── 2025-10-29/             # Date-based directories (created_at)
        │   ├── tshark-filtering.md
        │   ├── tshark-filtering.jsonl
        │   ├── rust-webgpu.md
        │   └── rust-webgpu.jsonl
        ├── 2025-10-28/
        │   └── ...
        └── .uuid-index.json        # UUID → path mapping
```

**File types:**

- `.md` - Human-readable markdown with YAML frontmatter
- `.jsonl` - Raw message records (one per line)
- `org.jsonl` - Organization metadata
- `.uuid-index.json` - Fast UUID → path lookup
- `.config.json` - Session key, preferences

**Staleness tracking:**

- File mtime = conversation.updated_at from API
- If `file.mtime < api.updated_at`, file is stale
- `chatfs-cache-get-convo` checks staleness, re-fetches if needed
- Direct filesystem reads (`cat`, Obsidian) bypass staleness check

See [cache-layer] for implementation details.

## Testing

**M1 API Layer testing:**

```bash
# Test individual tools
echo '{}' | chatfs-api-list-orgs | jq

# Test pipeline composition
chatfs-api-list-orgs | head -n 1 | \
  chatfs-api-list-convos | head -n 5 | \
  chatfs-api-get-convo | \
  chatfs-api-render-md > output.md
```

See [../../HACKING.md#running-tests] for full testing guide.

## Future Considerations

### M2: Cache/FS Layer

Add `chatfs-cache-*` commands that wrap `chatfs-api-*` with:
- Filesystem persistence to `./chatfs/` directory
- Staleness checking via mtime
- Lazy directory creation
- Cache invalidation

See [cache-layer] for design details.

### M3: CLI Layer

Add `chatfs` commands with human-friendly UX:
- Path-based interface (no UUIDs)
- Progress bars, colors, interactive prompts
- Error recovery and helpful messages

See [porcelain-layer] for UX design.

### M4+: Advanced Features

**Capnproto Migration**

When capnshell exists:
1. Define capnproto schemas for Org, Conversation, Message
2. Swap JSONL serialization for capnproto in API layer tools
3. Cache and CLI layers unchanged (abstraction holds)

**Write Operations**

Not yet designed (see [../../design-incubators/fork-representation/]):
- Append to conversation
- Fork conversation
- Amend messages

Blocked on fork representation decision (M3+ scope).

**Multi-Provider Support**

ChatGPT, Gemini support:
- Add `chatfs.providers.*` with provider-specific API clients
- API layer tools gain `--provider` flag
- Cache structure: `./chatfs/chatgpt/`, `./chatfs/gemini/`

See [development-plan.md] for milestone details.

## Related Documents

- [design-rationale.md] - Why these design choices
- [development-plan.md] - Implementation milestones
- [technical-design/] - Detailed subsystem documentation

[markdown-format]: technical-design/markdown-format.md
[provider-interface]: technical-design/provider-interface.md
[cache-layer]: technical-design/cache-layer.md
[porcelain-layer]: technical-design/porcelain-layer.md
[design-rationale.md]: design-rationale.md
[development-plan.md]: development-plan.md
[technical-design/]: technical-design/
