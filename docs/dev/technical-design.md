# Technical Design

**Last Updated:** 2025-11-01

**Status:** ⚠️ Pre-implementation - Technical details are soft and under
discussion. Data structures, APIs, and implementation specifics will be refined
during M1-CLAUDE.

**Read this when:**

- Understanding the four-layer architecture (`native`, `vfs`, `cache`, `cli`)
- Implementing M1-CLAUDE (`native/claude` layer) or M2-VFS (`vfs` layer) tools
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
- **`native/claude` (M1-CLAUDE):** Direct API wrapper, outputs raw Claude data as JSONL
- **`vfs` (M2-VFS):** Normalized schema across providers (Claude, ChatGPT, etc.)
- **`cache` (M3-CACHE):** Adds persistence, staleness checking, lazy loading
- **`cli` (M4-CLI):** Human-friendly UX with colors and progress bars

**Design characteristics:**

- **Composable:** Small tools that pipe together (Unix philosophy)
- **Layered:** Four independent layers with clear boundaries and responsibilities
- **Progressive:** Each layer builds on the previous, each independently useful
- **Learn-then-abstract:** M1-CLAUDE (concrete) informs M2-VFS (abstract) design
- **Future-proof:** JSONL → capnproto migration path
- **Multi-provider ready:** M2-VFS normalizes across Claude, ChatGPT, Gemini

## Architecture

chatfs is built in four layers, each implemented in separate milestones:

**Data flow:**

```
┌─────────────────────────────────────────┐
│         claude.ai API                   │
│    unofficial-claude-api (Vendored)     │
│    st1vms Python client                 │
└─────────────────┬───────────────────────┘
                  │ HTTP/TLS
┌─────────────────▼───────────────────────┐
│   Native Layer (M1-CLAUDE - Next)       │
│   chatfs-claude-list-orgs               │
│   chatfs-claude-list-convos             │
│   chatfs-claude-get-convo               │
│   chatfs-claude-render-md               │
│   Commands: chatfs-claude-*             │
│   Modules: chatfs.layer.native.claude.* │
└─────────────────┬───────────────────────┘
                  │ Raw API responses
┌─────────────────▼───────────────────────┐
│    VFS Layer (M2-VFS - Future)          │
│   chatfs-vfs-list-orgs --provider X     │
│   chatfs-vfs-list-convos                │
│   chatfs-vfs-get-convo                  │
│   chatfs-vfs-render-md                  │
│   Commands: chatfs-vfs-*                │
│   Modules: chatfs.layer.vfs.*           │
└─────────────────┬───────────────────────┘
                  │ Virtual FS
┌─────────────────▼───────────────────────┐
│    Cache/FS Layer (M3-CACHE - Future)   │
│   chatfs-cache-list-orgs                │
│   chatfs-cache-list-convos              │
│   chatfs-cache-get-convo                │
│   Commands: chatfs-cache-*              │
│   Modules: chatfs.layer.cache.*         │
└─────────────────┬───────────────────────┘
                  │ Lazy, Cached FS
┌─────────────────▼───────────────────────┐
│      CLI Layer (M4-CLI - Future)        │
│   chatfs-ls //claude.ai/Buck\ Evan/...  │
│   chatfs-cat //claude.ai/.../convo.md   │
│   Commands: chatfs-ls, chatfs-cat, etc. │
│   Modules: chatfs.layer.cli.*           │
└─────────────────────────────────────────┘
```

**Layer responsibilities:**

- **`native/claude`:** Stateless, outputs whatever claude.ai returns as JSONL. No normalization, no decisions.
- **`vfs`:** Normalized JSONL schema across providers (Claude, ChatGPT, etc.). Takes `--provider` flag.
- **`cache`:** Filesystem persistence, staleness checking, lazy loading. Wraps `vfs`.
- **`cli`:** Human-friendly commands, colors, progress bars, interactive features. Wraps `cache`.

**Why four layers?**
- Each layer independently useful (can use any layer directly with jq/Unix tools)
- Clear milestone boundaries (M1-CLAUDE→M2-VFS→M3-CACHE→M4-CLI)
- Learn-then-abstract: `native/claude` (concrete Claude API) informs `vfs` (abstract schema) design
- Allows users to choose abstraction level based on needs

## Components

### Native Layer (M1-CLAUDE - Next)

**Layer:** `native/claude`
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

**Purpose:** Learn what Claude API actually returns before designing `vfs` layer's normalized schema.

**API Client:**

The `native/claude` layer includes an API client wrapper:

```python
from chatfs.layer.native.claude.client import ClaudeClient

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

### VFS Layer (M2-VFS - Future)

**Layer:** `vfs`
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

**Normalized Models:**

The `vfs` layer owns the normalized data structures:

```python
from chatfs.layer.vfs.models import Org, Conversation, Message

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

### Cache/FS Layer (M3-CACHE - Future)

**Layer:** `cache`
**Milestone:** M3-CACHE
**Commands:** `chatfs-cache-*`
**Modules:** `chatfs.layer.cache.*`

**Responsibility:** Filesystem persistence, staleness checking, lazy directory creation. Wraps `vfs` layer.

**Examples:**

```bash
# Same interface as vfs layer, but with caching
chatfs-cache-list-orgs | jq
chatfs-cache-list-convos | jq
chatfs-cache-get-convo | chatfs-vfs-render-md > conversation.md
```

**Implementation:** Wraps `vfs` layer tools (chatfs-vfs-*), adds:

- Filesystem writes to `./chatfs/` directory structure
- Staleness checking via mtime comparison
- Lazy directory/file creation
- Cache invalidation based on `updated_at` fields

**Cache utilities:**

```python
from chatfs.layer.cache.manager import CacheManager

cache = CacheManager(base_path="./chatfs")
cache.ensure_org_dir(org_name="Buck Evan")
cache.write_conversation(path="...", messages=[...])
cache.is_stale(path="...", remote_updated_at="...")
```

See [cache-layer] for staleness logic and directory structure.

### CLI Layer (M4-CLI - Future)

**Layer:** `cli`
**Milestone:** M4-CLI
**Commands:** `chatfs-ls`, `chatfs-cat`, `chatfs-sync`, etc.
**Modules:** `chatfs.layer.cli.*`

**Responsibility:** Human-friendly CLI wrappers with rich UX. Wraps `cache` layer.

**Examples:**

```bash
# Absolute paths (// prefix, work anywhere)
chatfs-ls //claude.ai/Buck\ Evan/2025-10-29
chatfs-cat //claude.ai/Buck\ Evan/2025-10-29/tshark-filtering.md

# Relative paths (filesystem-like, inside chatfs-init directory)
chatfs-init ~/my-chats && cd ~/my-chats
chatfs-ls claude.ai/Buck\ Evan/2025-10-29

cd claude.ai/Buck\ Evan/2025-10-29/
chatfs-cat tshark-filtering.md
chatfs-ls .
```

**Path semantics:** `//provider/...` = absolute, everything else = relative to cwd (like filesystem paths).

**Note:** Subcommand interface (`chatfs ls` instead of `chatfs-ls`) is a future optional enhancement.

**Implementation:** Wraps `cache` layer tools (chatfs-cache-*), adds:

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

Similar pattern for `chatfs-cache-list-convos` and `chatfs-cache-get-convo`: check cache, call `vfs` layer if stale, write to filesystem, output JSONL.

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

## Beyond the Four Layers (M5-WRITE+)

Advanced features beyond the core four-layer architecture, planned for M5-WRITE and later milestones.

### Capnproto Migration

When capnshell exists:
1. Define capnproto schemas for Org, Conversation, Message
2. Swap JSONL serialization for capnproto in `native/claude`/`vfs` tools
3. `cache` and `cli` layers unchanged (abstraction holds)

### Write Operations

Not yet designed (see [design-incubators/fork-representation/]):
- Append to conversation
- Fork conversation
- Amend messages

Blocked on fork representation decision (M5-WRITE+ scope).

### Multi-Provider Support

Handled by `vfs` layer (see design-incubators/chat-provider-normalization/ and multi-domain-support/):
- `native/claude` layer exists (M1-CLAUDE milestone)
- Add `native/chatgpt` layer for ChatGPT (future milestone)
- Add `native/gemini` layer for Gemini (future milestone)
- `vfs` layer normalizes across all native layers
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
