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
│       ├── plumbing/       # Low-level JSONL tools (modules)
│       │   ├── list_orgs.py
│       │   ├── list_convos.py
│       │   ├── get_convo.py
│       │   └── render_md.py
│       ├── porcelain/      # User-facing commands (future)
│       ├── api.py          # API client
│       ├── cache.py        # Filesystem cache
│       └── models.py       # Data structures
└── docs/
    └── dev/                # Design documentation
        └── reference-implementations/  # Reference code (git submodules)
```

See [docs/dev/technical-design.md] for
architecture details.

## Running Tests

**Note:** The testing commands shown below will work after M0 configures entry points in pyproject.toml. For now, these serve as reference for post-M0 testing workflow.

**Test plumbing modules** (available after M0 entry point configuration):

```bash
uv sync  # one-time setup, for new modules
echo '{}' | chatfs-list-orgs | jq

# List conversations for org
echo '{"uuid":"org-uuid"}' | chatfs-list-convos | jq

# After installation - use CLI commands
chatfs-list-orgs | jq -r '.name'

# Pipe through entire flow
chatfs-list-orgs | head -n 1 | \
  chatfs-list-convos | head -n 5 | \
  chatfs-get-convo | \
  chatfs-render-md > output.md
```

**Testing with jq:**

```bash
# Extract specific fields
chatfs-list-orgs | jq -r '.name'

# Filter conversations
chatfs-list-convos | jq 'select(.created_at > "2025-10")'
```

## Common Tasks

### Adding a New Plumbing Tool

**Plumbing contract:**

- Read JSONL from stdin (one JSON object per line)
- Write JSONL to stdout
- Log errors to stderr
- Exit 0 on success
- No terminal dependencies (colors, progress bars, etc.)

**Example:**

```python
#!/usr/bin/env -S uv run
"""
chatfs-example-tool - Does something useful

Reads: {input_field: "value"}
Writes: {output_field: "result"}
"""
import sys
import json

def main():
    """CLI entry point for chatfs-example-tool command."""
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

1. Create module in `lib/chatfs/plumbing/example_tool.py`
2. Add `main()` function as entry point
3. Document input/output schema in module docstring
4. Add entry point to `pyproject.toml` to create `chatfs-example-tool` command
5. uv sync
6. Test with: `echo '{"test":"data"}' | chatfs-example-tool`

### Debugging API Issues

**Enable verbose logging:**

```python
# In lib/chatfs/api.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Inspect raw API responses:**

```bash
# Use chatfs-get-convo and save raw JSON
echo '{"uuid":"convo-uuid"}' | chatfs-get-convo > raw-response.jsonl
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

**Plumbing pipeline:**

```
chatfs-list-orgs
  → {uuid, name, created_at, ...}

chatfs-list-convos (stdin: org record)
  → {uuid, title, created_at, updated_at, org_uuid, ...}

chatfs-get-convo (stdin: convo record)
  → {type: "human", text: "...", created_at: "..."}
  → {type: "assistant", text: "...", created_at: "..."}

chatfs-render-md (stdin: message records)
  → Markdown output (not JSONL)
```

See
[docs/dev/technical-design.md#data-flow]
for details.

### Working with the Cache

**Cache location:** `./chatfs/` directory with org-based structure

**Staleness tracking:** Files have `mtime = conversation.updated_at` from API. If stale, re-fetch.

See [docs/dev/technical-design.md#filesystem-cache-structure] for detailed cache structure and invalidation logic.

## Architecture

**Plumbing/Porcelain Split:**

- **Plumbing:** Raw functionality, JSONL I/O, scriptable
- **Porcelain:** (Future) Nice UX, human-friendly paths, progress bars

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

See [docs/dev/design-rationale.md] for full
reasoning.

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
