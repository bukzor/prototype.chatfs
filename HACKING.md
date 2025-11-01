# Hacking on claifs

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
│   └── claifs/             # Main claifs package
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

See [docs/dev/technical-design.md](docs/dev/technical-design.md) for
architecture details.

## Running Tests

**Test plumbing modules:**

```bash
uv sync  # one-time setup, for new modules
echo '{}' | claifs-list-orgs | jq

# List conversations for org
echo '{"uuid":"org-uuid"}' | claifs-list-convos | jq

# After installation - use CLI commands
claifs-list-orgs | jq -r '.name'

# Pipe through entire flow
claifs-list-orgs | head -n 1 | \
  claifs-list-convos | head -n 5 | \
  claifs-get-convo | \
  claifs-render-md > output.md
```

**Testing with jq:**

```bash
# Extract specific fields
claifs-list-orgs | jq -r '.name'

# Filter conversations
claifs-list-convos | jq 'select(.created_at > "2025-10")'
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
claifs-example-tool - Does something useful

Reads: {input_field: "value"}
Writes: {output_field: "result"}
"""
import sys
import json

def main():
    """CLI entry point for claifs-example-tool command."""
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

1. Create module in `lib/claifs/plumbing/example_tool.py`
2. Add `main()` function as entry point
3. Document input/output schema in module docstring
4. Add entry point to `pyproject.toml` to create `claifs-example-tool` command
5. uv sync
6. Test with: `echo '{"test":"data"}' | claifs-example-tool`

### Debugging API Issues

**Enable verbose logging:**

```python
# In lib/claifs/api.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Inspect raw API responses:**

```bash
# Use claifs-get-convo and save raw JSON
echo '{"uuid":"convo-uuid"}' | claifs-get-convo > raw-response.jsonl
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
claifs-list-orgs
  → {uuid, name, created_at, ...}

claifs-list-convos (stdin: org record)
  → {uuid, title, created_at, updated_at, org_uuid, ...}

claifs-get-convo (stdin: convo record)
  → {type: "human", text: "...", created_at: "..."}
  → {type: "assistant", text: "...", created_at: "..."}

claifs-render-md (stdin: message records)
  → Markdown output (not JSONL)
```

See
[docs/dev/technical-design.md#data-flow](docs/dev/technical-design.md#data-flow)
for details.

### Working with the Cache

**Cache structure:**

```
./claudefs/
├── .config.json           # Session key, default org
└── claude.ai/
    └── Buck Evan/         # Organization name
        ├── org.jsonl      # Org metadata
        ├── 2025-10-29/    # Date-based directories
        │   ├── title.md
        │   └── title.jsonl
        └── .uuid-index.json
```

**Cache invalidation:**

- Files have `mtime = conversation.updated_at`
- If `file.mtime < api.updated_at`, re-fetch
- `claifs-sync` forces refresh regardless of mtime

See
[docs/dev/technical-design/caching-strategy.md](docs/dev/technical-design/caching-strategy.md)
for implementation.

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

See [docs/dev/design-rationale.md](docs/dev/design-rationale.md) for full
reasoning.

## Design Decisions

For detailed rationale on architectural choices, see:

- [docs/dev/design-rationale.md](docs/dev/design-rationale.md) - Core design
  decisions
- [docs/dev/technical-design.md](docs/dev/technical-design.md) - System
  architecture
- [design-incubators/](design-incubators/) - Unsolved problems being explored

## Contributing Workflow

1. Check [STATUS.md](STATUS.md) for current milestone
2. Read relevant design docs
3. Implement changes
4. Test with plumbing pipeline
5. Update documentation if needed

**For major changes:**

- Discuss in design-incubators/ first
- Prototype multiple approaches
- Document decision rationale
