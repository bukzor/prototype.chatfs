# Technical Design

**Last Updated:** 2025-11-01

**Status:** ⚠️ Pre-implementation - Technical details are soft and under
discussion. Data structures, APIs, and implementation specifics will be refined
during Milestone 1.

**Read this when:**

- Understanding how the system works
- Implementing a new component
- Debugging data flow issues
- Onboarding as a contributor

This document describes what claifs is and how it's architected.

## System Overview

claifs provides lazy filesystem access to claude.ai conversations through
composable JSONL-based plumbing tools.

**Key characteristics:**

- **Lazy:** Files/directories created only when accessed
- **Composable:** Small tools that pipe together (Unix philosophy)
- **Cached:** Filesystem stores conversation data, mtime tracks staleness
- **Offline-friendly:** Cached files work without network
- **Future-proof:** JSONL → capnproto migration path

## Architecture

```
┌─────────────────────────────────────────┐
│          Porcelain (Future)             │
│   claifs ls "Buck Evan/2025-10-29"      │
│   claifs cat "path/to/conversation.md"  │
└─────────────────┬───────────────────────┘
                  │ Uses
┌─────────────────▼───────────────────────┐
│         Plumbing (JSONL I/O)            │
│  claifs-list-orgs                       │
│  claifs-list-convos                     │
│  claifs-get-convo                       │
│  claifs-render-md                       │
└─────────────────┬───────────────────────┘
                  │ Uses
┌─────────────────▼───────────────────────┐
│        Shared Libraries                 │
│  lib/claifs/api.py     (API client)     │
│  lib/claifs/cache.py   (Filesystem)     │
│  lib/claifs/models.py  (Data structs)   │
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

## Components

### Plumbing Tools

**Responsibility:** Core data operations via JSONL stdin/stdout

**Interface:**

```bash
# Read JSONL from stdin, write JSONL to stdout
echo '{"uuid":"org-123"}' | claifs-list-convos | jq
```

**Tools:**

**claifs-list-orgs**

- Input: None (or `{}` empty object)
- Output: One JSON object per org per line
- Schema: `{uuid, name, created_at, ...}`

**claifs-list-convos**

- Input: Org record `{uuid, ...}`
- Output: One JSON object per conversation per line
- Schema: `{uuid, title, created_at, updated_at, org_uuid, ...}`

**claifs-get-convo**

- Input: Conversation record `{uuid, ...}`
- Output: One JSON object per message per line
- Schema: `{type: "human"|"assistant", text, created_at, ...}`

**claifs-render-md**

- Input: Message records (JSONL)
- Output: Markdown with YAML frontmatter (NOT JSONL)
- Format: See
  [technical-design/markdown-format.md]

See
[../../HACKING.md#adding-a-new-plumbing-tool]
for implementation guide.

### Shared Libraries

**lib/claifs/api.py** - API Client Wrapper

**Responsibility:** Wrap unofficial-claude-api, handle auth, normalize responses

**Interface:**

```python
from claifs.api import Client

client = Client()  # Uses CLAUDE_SESSION_KEY from env
orgs = client.list_organizations()
convos = client.list_conversations(org_uuid="...")
messages = client.get_conversation(convo_uuid="...")
```

**Key methods:**

- `list_organizations() → List[Org]`
- `list_conversations(org_uuid: str) → List[Conversation]`
- `get_conversation(convo_uuid: str) → List[Message]`

See [technical-design/api-reference.md] for
full API documentation.

**lib/claifs/cache.py** - Filesystem Cache

**Responsibility:** Manage filesystem cache, track staleness via mtime, lazy
creation

**Interface:**

```python
from claifs.cache import Cache

cache = Cache(base_path="./claudefs")
cache.ensure_org_dir(org_name="Buck Evan")
cache.write_conversation(path="...", messages=[...])
cache.is_stale(path="...", remote_updated_at="...")
```

**Key methods:**

- `ensure_dir(path: str) → None` - Create directory if not exists
- `write_conversation(path: str, messages: List[Message]) → None`
- `is_stale(path: str, remote_updated_at: datetime) → bool`
- `create_stub(path: str, mtime: datetime) → None` - Empty file with mtime

See [technical-design/caching-strategy.md]
for staleness logic.

**lib/claifs/models.py** - Data Structures

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

### Porcelain (Future)

**Responsibility:** Human-friendly CLI wrappers

**Examples:**

```bash
claifs ls "Buck Evan"               # List conversations
claifs cat "path/to/convo.md"       # Read conversation
claifs sync "Buck Evan/2025-10"     # Force refresh
```

**Implementation:** Uses plumbing tools under the hood, adds:

- Path parsing (org name → org UUID)
- Progress bars
- Colors/formatting
- Error messages

See [technical-design/porcelain-design.md]
for UX design.

## Data Flow

### List Organizations

```
claifs-list-orgs
  ↓
lib/claifs/api.Client.list_organizations()
  ↓
unofficial-claude-api HTTP request
  ↓
claude.ai API response
  ↓
lib/claifs/models.Org objects
  ↓
JSONL output: {"uuid": "...", "name": "Buck Evan", ...}
```

### List Conversations for Org

```
echo '{"uuid":"org-123"}' | claifs-list-convos
  ↓
Parse JSONL stdin → org_uuid
  ↓
lib/claifs/api.Client.list_conversations(org_uuid)
  ↓
unofficial-claude-api HTTP request
  ↓
claude.ai API response
  ↓
lib/claifs/models.Conversation objects
  ↓
JSONL output: {"uuid": "...", "title": "...", "created_at": "...", ...}
```

### Get Conversation Messages

```
echo '{"uuid":"convo-456"}' | claifs-get-convo
  ↓
Parse JSONL stdin → convo_uuid
  ↓
lib/claifs/api.Client.get_conversation(convo_uuid)
  ↓
unofficial-claude-api HTTP request
  ↓
claude.ai API response
  ↓
lib/claifs/models.Message objects
  ↓
JSONL output: {"type": "human", "text": "...", ...}
                {"type": "assistant", "text": "...", ...}
```

### Render to Markdown

```
claifs-get-convo | claifs-render-md
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

## Filesystem Cache Structure

```
./claudefs/
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
- `claifs-cat` checks staleness before reading
- Regular `cat` bypasses check (shows cached data)

See [technical-design/caching-strategy.md]
for details.

## Testing

See [../../HACKING.md#running-tests] for testing approach and examples.

## Future Considerations

### Capnproto Migration

When capnshell exists:

1. Define capnproto schemas for Org, Conversation, Message
2. Swap JSONL serialization for capnproto in plumbing tools
3. Porcelain layer unchanged (abstraction holds)

### Write Operations

Not yet designed (see
[../../design-incubators/fork-representation/]):

- Append to conversation
- Fork conversation
- Amend messages

Blocked on fork representation decision.

### Multi-Provider Support

ChatGPT, Gemini support:

- Add `lib/claifs/providers/` with provider-specific API clients
- Plumbing tools gain `--provider` flag
- Cache structure: `./claudefs/chatgpt/`, `./claudefs/gemini/`

See [development-plan.md#milestone-2].

## Related Documents

- [design-rationale.md] - Why these design choices
- [development-plan.md] - Implementation milestones
- [technical-design/] - Detailed subsystem documentation
