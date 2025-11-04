# Technical Design

**Last Updated:** 2025-11-01

**Status:** ⚠️ Pre-implementation - Technical details are soft and under
discussion. Data structures, APIs, and implementation specifics will be refined
during Milestone 1.

**Read this when:**

- Understanding the four-layer architecture (Native/VFS/Cache/CLI)
- Implementing M1-CLAUDE (claude-native layer) or M2-VFS (normalized layer) tools
- Understanding data flow and component interactions
- Planning M2-VFS/M3-CACHE/M4-CLI implementation
- Onboarding as a contributor

This document describes chatfs's architecture and milestone-based implementation plan.

## System Overview

chatfs provides programmatic access to claude.ai conversations through composable JSONL-based tools, built in four layers (Native, VFS, Cache, CLI).

**Current state (M0-DOCS):**
- Documentation phase - no implementation yet
- Next: M1-CLAUDE (claude-native layer)

**Planned layers:**
- **M1-CLAUDE:** Claude-native layer - direct API wrapper, outputs raw Claude data as JSONL
- **M2-VFS:** Virtual filesystem layer - normalized schema across providers (Claude, ChatGPT, etc.)
- **M3-CACHE:** Cache/filesystem layer - adds persistence, staleness checking, lazy loading
- **M4-CLI:** CLI layer - human-friendly UX with colors and progress bars

**Design characteristics:**

- **Composable:** Small tools that pipe together (Unix philosophy)
- **Layered:** Four independent layers with clear boundaries and responsibilities
- **Progressive:** Each layer builds on the previous, each independently useful
- **Learn-then-abstract:** M1-CLAUDE (concrete) informs M2-VFS (abstract) design
- **Future-proof:** JSONL → capnproto migration path
- **Multi-provider ready:** M2-VFS normalizes across Claude, ChatGPT, Gemini

## Architecture

chatfs is built in four layers, each implemented in separate milestones:

```
┌─────────────────────────────────────────┐
│      CLI Layer (M4-CLI - Future)        │
│   chatfs ls "Buck Evan/2025-10-29"      │
│   chatfs cat "path/to/conversation.md"  │
│   Commands: chatfs <subcommand>         │
│   Modules: chatfs.layer.cli.*           │
└─────────────────┬───────────────────────┘
                  │ Uses
┌─────────────────▼───────────────────────┐
│    Cache/FS Layer (M3-CACHE - Future)   │
│   chatfs-cache-list-orgs                │
│   chatfs-cache-list-convos              │
│   chatfs-cache-get-convo                │
│   Commands: chatfs-cache-*              │
│   Modules: chatfs.layer.cache.*         │
└─────────────────┬───────────────────────┘
                  │ Uses
┌─────────────────▼───────────────────────┐
│    VFS Layer (M2-VFS - Future)          │
│   chatfs-vfs-list-orgs --provider X     │
│   chatfs-vfs-list-convos                │
│   chatfs-vfs-get-convo                  │
│   chatfs-vfs-render-md                  │
│   Commands: chatfs-vfs-*                │
│   Modules: chatfs.layer.vfs.*           │
└─────────────────┬───────────────────────┘
                  │ Uses
┌─────────────────▼───────────────────────┐
│   Native Layer (M1-CLAUDE - Next)       │
│   chatfs-claude-list-orgs               │
│   chatfs-claude-list-convos             │
│   chatfs-claude-get-convo               │
│   chatfs-claude-render-md               │
│   Commands: chatfs-claude-*             │
│   Modules: chatfs.layer.native.claude.* │
└─────────────────┬───────────────────────┘
                  │ Uses
┌─────────────────▼───────────────────────┐
│        Shared Libraries                 │
│  chatfs.client   (Claude API wrapper)   │
│  chatfs.models   (M2-VFS data models)   │
│  chatfs.cache    (M3-CACHE manager)     │
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

- **M1-CLAUDE (Native):** Stateless, outputs whatever claude.ai returns as JSONL. No normalization, no decisions.
- **M2-VFS (Virtual FS):** Normalized JSONL schema across providers (Claude, ChatGPT, etc.). Takes `--provider` flag.
- **M3-CACHE (Cache/FS):** Filesystem persistence, staleness checking, lazy loading. Wraps M2-VFS.
- **M4-CLI (CLI):** Human-friendly commands, colors, progress bars, interactive features. Wraps M3-CACHE.

**Why four layers?**
- Each layer independently useful (can use any layer directly with jq/Unix tools)
- Clear milestone boundaries (M1-CLAUDE→M2-VFS→M3-CACHE→M4-CLI)
- Learn-then-abstract: M1-CLAUDE (concrete Claude API) informs M2-VFS (abstract schema) design
- Allows users to choose abstraction level based on needs

## Components

### Native Layer (M1-CLAUDE - Next)

**Milestone:** M1-CLAUDE
**Commands:** `chatfs-claude-*`
**Modules:** `chatfs.layer.native.claude.*`

**Responsibility:** Direct wrapper around claude.ai API. Outputs whatever Claude returns as JSONL, with minimal processing. No normalization decisions.

**Interface:**

```bash
# Read JSONL from stdin, write JSONL to stdout
echo '{}' | chatfs-claude-list-orgs | jq
echo '{"uuid":"org-123"}' | chatfs-claude-list-convos | jq
```

**Tools:**

**chatfs-claude-list-orgs** (`chatfs.layer.native.claude.list_orgs`)

- Input: None required (can accept `{}` on stdin, but ignores it; starting point for pipelines)
- Output: One JSON object per org per line (raw Claude API response as JSONL)
- Behavior: Calls API every time (no caching)

**chatfs-claude-list-convos** (`chatfs.layer.native.claude.list_convos`)

- Input: Org record `{uuid, ...}`
- Output: One JSON object per conversation per line (raw Claude API response as JSONL)
- Behavior: Calls API every time (no caching)

**chatfs-claude-get-convo** (`chatfs.layer.native.claude.get_convo`)

- Input: Conversation record `{uuid, ...}`
- Output: One JSON object per message per line (raw Claude API response as JSONL)
- Behavior: Calls API every time (no caching)

**chatfs-claude-render-md** (`chatfs.layer.native.claude.render_md`)

- Input: Message records (JSONL)
- Output: Markdown with YAML frontmatter (NOT JSONL)
- Behavior: Pure transformation, no API calls

**Contract:**
- Read JSONL from stdin (except list-orgs)
- Write JSONL to stdout (except render-md → markdown)
- Log errors to stderr
- Exit 0 on success
- No terminal dependencies (no colors, progress bars)
- No filesystem interaction (stateless)
- **Minimal abstraction:** Output whatever Claude API returns, don't normalize

**Purpose:** Learn what Claude API actually returns before designing M2-VFS normalized schema.

### VFS Layer (M2-VFS - Future)

**Milestone:** M2-VFS
**Commands:** `chatfs-vfs-*`
**Modules:** `chatfs.layer.vfs.*`

**Responsibility:** Normalized JSONL schema across providers (Claude, ChatGPT, etc.). Stateless, no filesystem writes.

**Interface:**

```bash
# Read JSONL from stdin, write JSONL to stdout
echo '{"provider":"claude"}' | chatfs-vfs-list-orgs | jq
echo '{"uuid":"org-123"}' | chatfs-vfs-list-convos | jq
```

**Tools:**

**chatfs-vfs-list-orgs** (`chatfs.layer.vfs.list_orgs`)

- Input: `{provider: "claude"|"chatgpt", ...}` (or uses default provider)
- Output: One JSON object per org per line (normalized schema)
- Schema: `{uuid, name, created_at, ...}` (provider-agnostic)
- Behavior: Calls appropriate native layer (chatfs-claude-*, chatfs-chatgpt-*), normalizes output

**chatfs-vfs-list-convos** (`chatfs.layer.vfs.list_convos`)

- Input: Org record `{uuid, ...}` (normalized schema)
- Output: One JSON object per conversation per line (normalized schema)
- Schema: `{uuid, title, created_at, updated_at, org_uuid, ...}` (provider-agnostic)
- Behavior: Calls native layer, normalizes output

**chatfs-vfs-get-convo** (`chatfs.layer.vfs.get_convo`)

- Input: Conversation record `{uuid, ...}` (normalized schema)
- Output: One JSON object per message per line (normalized schema)
- Schema: `{type: "human"|"assistant", text, created_at, ...}` (provider-agnostic)
- Behavior: Calls native layer, normalizes output

**chatfs-vfs-render-md** (`chatfs.layer.vfs.render_md`)

- Input: Message records (JSONL, normalized schema)
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
- **Normalized schema:** Provider-agnostic data structures

### Shared Libraries

**chatfs.client** - Claude API Client Wrapper (M1-CLAUDE)

**Responsibility:** Wrap unofficial-claude-api, handle auth. Used by M1-CLAUDE layer.

**Interface:**

```python
from chatfs.client import ClaudeClient

client = ClaudeClient()  # Uses CLAUDE_SESSION_KEY from env
orgs = client.list_organizations()
convos = client.list_conversations(org_uuid="...")
messages = client.get_conversation(convo_uuid="...")
```

**Key methods:**

- `list_organizations() → List[Dict]` (returns raw API response)
- `list_conversations(org_uuid: str) → List[Dict]`
- `get_conversation(convo_uuid: str) → List[Dict]`

See [provider-interface] for full API documentation.

**chatfs.models** - Normalized Data Structures (M2-VFS)

**Responsibility:** Type definitions for normalized schema. Defined at M2-VFS layer.

**Structures:**

```python
@dataclass
class Org:
    uuid: str
    name: str
    created_at: datetime
    provider: str  # "claude", "chatgpt", etc.

@dataclass
class Conversation:
    uuid: str
    title: str
    created_at: datetime
    updated_at: datetime
    org_uuid: str
    provider: str

@dataclass
class Message:
    type: Literal["human", "assistant"]
    text: str
    created_at: datetime
    uuid: str
```

**chatfs.cache** - Filesystem Cache Manager (M3-CACHE)

**Responsibility:** Filesystem operations, staleness checking. Used by M3-CACHE layer.

```python
from chatfs.cache import Cache

cache = Cache(base_path="./chatfs")
cache.ensure_org_dir(org_name="Buck Evan")
cache.write_conversation(path="...", messages=[...])
cache.is_stale(path="...", remote_updated_at="...")
```

See [cache-layer] for implementation details.

### Cache/FS Layer (M3-CACHE - Future)

**Milestone:** M3-CACHE
**Commands:** `chatfs-cache-*`
**Modules:** `chatfs.layer.cache.*`

**Responsibility:** Filesystem persistence, staleness checking, lazy directory creation. Wraps M2-VFS.

**Examples:**

```bash
# Same interface as VFS layer, but with caching
chatfs-cache-list-orgs | jq
chatfs-cache-list-convos | jq
chatfs-cache-get-convo | chatfs-vfs-render-md > conversation.md
```

**Implementation:** Wraps M2-VFS layer tools (chatfs-vfs-*), adds:

- Filesystem writes to `./chatfs/` directory structure
- Staleness checking via mtime comparison
- Lazy directory/file creation
- Cache invalidation based on `updated_at` fields

See [cache-layer] for staleness logic and directory structure.

### CLI Layer (M4-CLI - Future)

**Milestone:** M4-CLI
**Commands:** `chatfs <subcommand>` (no prefix)
**Modules:** `chatfs.layer.cli.*`

**Responsibility:** Human-friendly CLI wrappers with rich UX. Wraps M3-CACHE.

**Examples:**

```bash
chatfs ls "Buck Evan"               # List conversations
chatfs cat "path/to/convo.md"       # Read conversation
chatfs sync "Buck Evan/2025-10"     # Force refresh
```

**Implementation:** Wraps M3-CACHE layer tools (chatfs-cache-*), adds:

- Path parsing (org name → org UUID lookup)
- Progress bars for slow operations
- Colors/formatting for terminal output
- Friendly error messages
- Interactive prompts

See [cli-layer] for UX design.

## Data Flow

### M1-CLAUDE: Native Layer (Stateless)

**List Organizations**

```
chatfs-claude-list-orgs
  ↓
chatfs.client.ClaudeClient.list_organizations()
  ↓
unofficial-claude-api HTTP request
  ↓
claude.ai API response (raw)
  ↓
Serialize to JSONL stdout (minimal processing)
  ↓
Output: {"uuid": "...", "name": "Buck Evan", ...} (whatever Claude returns)
```

**List Conversations for Org**

```
echo '{"uuid":"org-123"}' | chatfs-claude-list-convos
  ↓
Parse JSONL stdin → org_uuid
  ↓
chatfs.client.ClaudeClient.list_conversations(org_uuid)
  ↓
unofficial-claude-api HTTP request
  ↓
claude.ai API response (raw)
  ↓
Serialize to JSONL stdout (minimal processing)
  ↓
Output: {"uuid": "...", "title": "...", ...} (whatever Claude returns)
```

**Get Conversation Messages**

```
echo '{"uuid":"convo-456"}' | chatfs-claude-get-convo
  ↓
Parse JSONL stdin → convo_uuid
  ↓
chatfs.client.ClaudeClient.get_conversation(convo_uuid)
  ↓
unofficial-claude-api HTTP request
  ↓
claude.ai API response (raw)
  ↓
Serialize to JSONL stdout (minimal processing)
  ↓
Output: {"type": "human", "text": "...", ...} (whatever Claude returns)
```

### M2-VFS: Virtual FS Layer (Normalized, Stateless)

**List Organizations (Normalized)**

```
echo '{"provider":"claude"}' | chatfs-vfs-list-orgs
  ↓
Determine provider from input (or use default)
  ↓
Call: chatfs-claude-list-orgs (subprocess)
  ↓
Parse raw JSONL output
  ↓
Normalize to provider-agnostic schema (chatfs.models.Org)
  ↓
Serialize to JSONL stdout
  ↓
Output: {"uuid": "...", "name": "Buck Evan", "provider": "claude", ...}
```

**List Conversations (Normalized)**

```
echo '{"uuid":"org-123", "provider":"claude"}' | chatfs-vfs-list-convos
  ↓
Call: echo '{"uuid":"org-123"}' | chatfs-claude-list-convos
  ↓
Normalize to provider-agnostic schema (chatfs.models.Conversation)
  ↓
Output: {"uuid": "...", "title": "...", "provider": "claude", ...}
```

Similar pattern for `chatfs-vfs-get-convo` and `chatfs-vfs-render-md`: call native layer, normalize output.

### M3-CACHE: Cache/FS Layer (With Persistence)

**List Organizations (Cached)**

```
chatfs-cache-list-orgs
  ↓
chatfs.cache.Cache.is_stale("./chatfs/orgs.jsonl")
  ↓ (if stale or missing)
Call: chatfs-vfs-list-orgs (subprocess)
  ↓
Parse output, write to ./chatfs/orgs.jsonl
  ↓
Set mtime to current time
  ↓
Output cached JSONL
```

Similar pattern for `chatfs-cache-list-convos` and `chatfs-cache-get-convo`: check cache, call M2-VFS layer if stale, write to filesystem, output JSONL.

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

## Filesystem Cache Structure (M3-CACHE - Future)

**Milestone:** M3-CACHE (not implemented in M1-CLAUDE or M2-VFS)

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

**M1-CLAUDE Native Layer testing:**

```bash
# Test individual tools
echo '{}' | chatfs-claude-list-orgs | jq

# Test pipeline composition
chatfs-claude-list-orgs | head -n 1 | \
  chatfs-claude-list-convos | head -n 5 | \
  chatfs-claude-get-convo | \
  chatfs-claude-render-md > output.md
```

**M2-VFS Normalized Layer testing:**

```bash
# Test with provider flag
echo '{"provider":"claude"}' | chatfs-vfs-list-orgs | jq

# Test pipeline with normalization
chatfs-vfs-list-orgs | head -n 1 | \
  chatfs-vfs-list-convos | \
  chatfs-vfs-get-convo | \
  chatfs-vfs-render-md > output.md
```

See [../../HACKING.md#running-tests] for full testing guide.

## Future Considerations

### M2-VFS: Virtual Filesystem Layer

Add `chatfs-vfs-*` commands that normalize across providers:
- Wrap M1-CLAUDE (chatfs-claude-*) tools with normalization layer
- Add provider abstraction for ChatGPT, Gemini
- Define normalized JSONL schema based on M1-CLAUDE findings
- `--provider` flag to select provider

See design-incubators/provider-abstraction-strategy/ for abstraction design.

### M3-CACHE: Cache/FS Layer

Add `chatfs-cache-*` commands that wrap `chatfs-vfs-*` with:
- Filesystem persistence to `./chatfs/` directory
- Staleness checking via mtime
- Lazy directory creation
- Cache invalidation

See [cache-layer] for design details.

### M4-CLI: CLI Layer

Add `chatfs` commands with human-friendly UX:
- Path-based interface (no UUIDs)
- Progress bars, colors, interactive prompts
- Error recovery and helpful messages

See [cli-layer] for UX design.

### M5-WRITE+: Advanced Features

**Capnproto Migration**

When capnshell exists:
1. Define capnproto schemas for Org, Conversation, Message
2. Swap JSONL serialization for capnproto in M1-CLAUDE/M2-VFS tools
3. M3-CACHE and M4-CLI layers unchanged (abstraction holds)

**Write Operations**

Not yet designed (see [../../design-incubators/fork-representation/]):
- Append to conversation
- Fork conversation
- Amend messages

Blocked on fork representation decision (M5-WRITE+ scope).

**Multi-Provider Support**

Handled by M2-VFS layer (see design-incubators/provider-abstraction-strategy/):
- M1-CLAUDE native layer exists
- Add M1-CHATGPT native layer for ChatGPT
- Add M1-GEMINI native layer for Gemini
- M2-VFS layer normalizes across all native layers
- Cache structure: `./chatfs/chatgpt/`, `./chatfs/gemini/`, `./chatfs/claude.ai/`

See [development-plan.md] for milestone details.

## Related Documents

- [design-rationale.md] - Why these design choices
- [development-plan.md] - Implementation milestones
- [technical-design/] - Detailed subsystem documentation

[markdown-format]: technical-design/markdown-format.md
[provider-interface]: technical-design/provider-interface.md
[cache-layer]: technical-design/cache-layer.md
[cli-layer]: technical-design/cli-layer.md
[design-rationale.md]: design-rationale.md
[development-plan.md]: development-plan.md
[technical-design/]: technical-design/
