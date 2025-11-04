# Hacking on chatfs

**Last Updated:** 2025-11-01

## Setup

**Prerequisites:**

- Python 3.10+
- uv (Python package manager)
- Claude.ai session key

**Install dependencies:**

```bash
cd claude-api
uv sync
```

**Get session key:**

1. Log into claude.ai in your browser
2. Open browser DevTools → Application → Cookies
3. Copy the `sessionKey` cookie value
4. Store in `.env`: `CLAUDE_SESSION_KEY=sk-ant-...`

## Project Structure

```
claude-api/
├── lib/
│   └── chatfs/             # Main chatfs package
│       ├── layer/
│       │   ├── native/
│       │   │   └── claude/  # M1-CLAUDE: Claude-native tools
│       │   │       ├── list_orgs.py
│       │   │       ├── list_convos.py
│       │   │       ├── get_convo.py
│       │   │       └── render_md.py
│       │   ├── vfs/         # M2-VFS: Normalized JSONL tools (future)
│       │   ├── cache/       # M3-CACHE: Persistent storage (future)
│       │   └── cli/         # M4-CLI: Human-friendly commands (future)
│       ├── client.py        # API client wrapper
│       ├── cache.py         # Filesystem cache
│       └── models.py        # Data structures
└── docs/
    └── dev/                 # Design documentation
        └── reference-implementations/  # Reference code (git submodules)
```

See [docs/dev/technical-design.md] for
architecture details.

## Running Tests

**Note:** The testing commands shown below will work after M0-DOCS configures entry points in pyproject.toml. For now, these serve as reference for post-M0-DOCS testing workflow.

**Test M1-CLAUDE layer** (Claude-native, outputs raw API data):

```bash
uv sync  # one-time setup, for new modules

# List organizations
echo '{}' | chatfs-claude-list-orgs | jq

# List conversations for org
echo '{"uuid":"org-uuid"}' | chatfs-claude-list-convos | jq

# Get conversation messages
echo '{"uuid":"convo-uuid"}' | chatfs-claude-get-convo | jq

# Pipe through entire flow
chatfs-claude-list-orgs | head -n 1 | \
  chatfs-claude-list-convos | head -n 5 | \
  chatfs-claude-get-convo | \
  chatfs-claude-render-md > output.md
```

**Test M2-VFS layer** (normalized, future):

```bash
# Same tools, normalized JSONL schema
chatfs-vfs-list-orgs | jq
chatfs-vfs-list-convos | jq
```

**Testing with jq:**

```bash
# Extract specific fields
chatfs-claude-list-orgs | jq -r '.name'

# Filter conversations
chatfs-claude-list-convos | jq 'select(.created_at > "2025-10")'
```

## Common Tasks

### Adding a New Layer Tool

**JSONL layer contract** (M1-CLAUDE, M2-VFS, M3-CACHE):

- Read JSONL from stdin (one JSON object per line)
- Write JSONL to stdout (except render-md → markdown)
- Log errors to stderr
- Exit 0 on success
- No terminal dependencies (colors, progress bars, etc.)

**Example:**

```python
#!/usr/bin/env -S uv run
"""
chatfs-{layer}-example-tool - Does something useful

Reads: {input_field: "value"}
Writes: {output_field: "result"}
"""
import sys
import json

def main():
    """CLI entry point for chatfs-{layer}-example-tool command."""
    for line in sys.stdin:
        input_obj = json.loads(line)

        # Do something with input_obj
        result = example_tool(input_obj)

        # Write JSONL to stdout
        print(json.dumps(result))

if __name__ == "__main__":
    main()
```

**Steps:**

1. Choose layer: native/claude/, vfs/, or cache/
2. Create module in `lib/chatfs/layer/{layer}/example_tool.py`
3. Add `main()` function as entry point
4. Document input/output schema in module docstring
5. Add entry point to `pyproject.toml`:
   - M1-CLAUDE: `chatfs-claude-example-tool`
   - M2-VFS: `chatfs-vfs-example-tool`
   - M3-CACHE: `chatfs-cache-example-tool`
6. Run `uv sync`
7. Test with: `echo '{"test":"data"}' | chatfs-{layer}-example-tool`

### Debugging API Issues

**Enable verbose logging:**

```python
# In lib/chatfs/client.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Inspect raw API responses:**

```bash
# Use chatfs-claude-get-convo and save raw JSON
echo '{"uuid":"convo-uuid"}' | chatfs-claude-get-convo > raw-response.jsonl
jq -s '.' raw-response.jsonl > formatted.json
```

**Test unofficial-claude-api directly:**

```python
# In Python REPL
from unofficial_claude_api import Client
client = Client()  # Uses CLAUDE_SESSION_KEY from env
orgs = client.list_organizations()
print(orgs)
```

### Understanding Data Flow

**M1-CLAUDE pipeline** (Claude-native):

```
chatfs-claude-list-orgs
  → {uuid, name, created_at, ...}

chatfs-claude-list-convos (stdin: org record)
  → {uuid, title, created_at, updated_at, org_uuid, ...}

chatfs-claude-get-convo (stdin: convo record)
  → {type: "human", text: "...", created_at: "..."}
  → {type: "assistant", text: "...", created_at: "..."}

chatfs-claude-render-md (stdin: message records)
  → Markdown output (not JSONL)
```

**M2-VFS pipeline** (normalized, future):

```
chatfs-vfs-list-orgs --provider=claude
  → {uuid, name, created_at, ...}  # Normalized schema

Same data flow, normalized JSONL across providers
```

See
[docs/dev/technical-design.md#data-flow]
for details.

### Working with the Cache

**Cache location:** `./chatfs/` directory with org-based structure

**Staleness tracking:** Files have `mtime = conversation.updated_at` from API. If stale, re-fetch.

See [docs/dev/technical-design.md#filesystem-cache-structure] for detailed cache structure and invalidation logic.

## Architecture

**Four-Layer Architecture:**

- **M1-CLAUDE (native):** Claude-native layer - outputs raw API data as JSONL, no normalization
- **M2-VFS (normalized):** Virtual filesystem layer - normalized JSONL schema across providers (Claude, ChatGPT)
- **M3-CACHE (persistence):** Cache/filesystem layer - persistent storage with staleness tracking
- **M4-CLI (UX):** CLI layer - human-friendly commands with colors, progress bars, path-based interface

**Why this layered approach?**

- **Learn then abstract:** Can't design good abstraction (M2-VFS) without understanding concrete case (M1-CLAUDE)
- **Clear separation:** Each layer has single responsibility
- **Testable:** JSONL layers (M1-M3) are pure stdin/stdout, easy to test with echo and jq

**Why JSONL?**

- Streaming-friendly (process line-by-line)
- Works with jq and standard Unix tools
- Easy migration to capnproto later
- Simple testing (echo JSON, check output)

**Why lazy loading?**

- Users have 100s-1000s of conversations
- Most are never accessed
- Fetch on-demand keeps everything fast
- Filesystem mtime tracks staleness

See [docs/dev/design-rationale.md] for full reasoning.

## Design Decisions

For detailed rationale on architectural choices, see:

- [docs/dev/design-rationale.md] - Core design
  decisions
- [docs/dev/technical-design.md] - System
  architecture
- [design-incubators/] - Unsolved problems being explored

## Contributing Workflow

1. Check [STATUS.md] for current milestone
2. Read relevant design docs
3. Implement changes
4. Test with plumbing pipeline
5. Update documentation if needed

**For major changes:**

- Discuss in design-incubators/ first
- Prototype multiple approaches
- Document decision rationale
