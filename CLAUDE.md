# claifs - Development Guide for Claude

**Last Updated:** 2025-11-01

## Quick Reference

**Testing plumbing modules** (commands available after M0 configures entry points):

```bash
echo '{}' | claifs-list-orgs | jq
echo '{"uuid":"org-uuid"}' | claifs-list-convos | jq
```

For _new_ plumbing, use `uv sync` to install.
Use echo + pipe + jq. Example: `echo '{"uuid":"abc"}' | claifs-list-convos | jq`. See [HACKING.md#running-tests].

**Working with unofficial API:**
Wrapped in `lib/claifs/api.py`. Uses curl_cffi for Cloudflare bypass. Raw access: `from unofficial_claude_api import Client`. See [docs/dev/technical-design/api-reference.md].

**Current state:** See [STATUS.md] for milestone, blockers, and next actions.

## Architecture Overview

claifs provides lazy filesystem access to claude.ai conversations. Built on plumbing/porcelain split: small JSONL tools (plumbing) compose with Unix tools, future nice UX wrappers (porcelain).

**Why JSONL:** Streaming-friendly, works with Unix tools now, easy capnproto migration later.

**Key subsystems:**

- **API client** (`lib/claifs/api.py`): Wraps unofficial-claude-api, handles auth. See [docs/dev/technical-design/api-reference.md].
- **Cache layer** (`lib/claifs/cache.py`): Filesystem operations, mtime tracking, lazy creation (design TODO).
- **Plumbing tools** (`lib/claifs/plumbing/`): JSONL-based modules for raw operations. See [docs/dev/technical-design.md#plumbing-tools].
- **Porcelain** (`lib/claifs/porcelain/`, future): Human-friendly wrappers. See [docs/dev/technical-design/porcelain-design.md].

## Data Flow

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

See [docs/dev/technical-design.md#data-flow] for details.

## Key Files

- `lib/claifs/plumbing/` - JSONL-based modules (list_orgs, list_convos, get_convo, render_md)
- `lib/claifs/api.py` - API client wrapper (wraps unofficial-claude-api)
- `lib/claifs/cache.py` - Filesystem cache (design TODO)
- `lib/claifs/models.py` - Data structures (Org, Conversation, Message)
- `docs/dev/` - Design documentation
- `design-incubators/fork-representation/` - Unsolved fork representation problem

## Conventions

**File naming:**

- Plumbing modules: `lib/claifs/plumbing/verb_noun.py` (e.g., `list_orgs.py`)
- CLI commands (via packaging): `claifs-verb-noun` (e.g., `claifs-list-orgs`)
- Libraries: `lib/claifs/noun.py` (e.g., `lib/claifs/cache.py`)
- Design docs: `docs/dev/category/topic.md` (e.g., `docs/dev/technical-design/api-reference.md`)

**JSONL format:**

- One JSON object per line
- UTF-8 encoding
- Streaming-friendly (process line-by-line)
- Works with jq: `claifs-list-orgs | jq -r '.name'`

**Plumbing contract:**

- Read JSONL from stdin
- Write JSONL to stdout (except render-md → markdown)
- Log errors to stderr
- Exit 0 on success
- No terminal dependencies (colors, progress bars)

## Testing

**Plumbing pipeline:**

```bash
# Test individual tools
echo '{}' | claifs-list-orgs | jq

# Test full pipeline
claifs-list-orgs | head -n 1 | \
  claifs-list-convos | head -n 5 | \
  claifs-get-convo | \
  claifs-render-md > output.md
```

See [HACKING.md#running-tests] for details.
