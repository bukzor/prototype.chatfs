# chatfs - Development Guide for Claude

**Last Updated:** 2025-11-01

## Quick Reference

**Testing plumbing modules** (commands available after M0-DOCS configures entry points):

M1-CLAUDE layer (claude-native, outputs raw API data):
```bash
echo '{}' | chatfs-claude-list-orgs | jq
echo '{"uuid":"org-uuid"}' | chatfs-claude-list-convos | jq
echo '{"uuid":"convo-uuid"}' | chatfs-claude-get-convo | jq
echo '{}' | chatfs-claude-list-orgs | head -n1 | chatfs-claude-list-convos | head -n1 | chatfs-claude-get-convo | chatfs-claude-render-md
```

For _new_ plumbing, use `uv sync` to install.
Use echo + pipe + jq. Example: `echo '{"uuid":"abc"}' | chatfs-claude-list-convos | jq`. See [HACKING.md#running-tests].

**Working with unofficial API:**
Wrapped in `lib/chatfs/api.py`. Uses curl_cffi for Cloudflare bypass. Raw access: `from unofficial_claude_api import Client`. See [docs/dev/technical-design/provider-interface.md].

**Current state:** See [STATUS.md] for milestone, blockers, and next actions.

## Architecture Overview

chatfs provides lazy filesystem access to chat conversations (claude.ai, ChatGPT). Built on plumbing/porcelain split: small JSONL tools (plumbing) compose with Unix tools, future nice UX wrappers (porcelain).

**Why JSONL:** Streaming-friendly, works with Unix tools now, easy capnproto migration later.

**Key subsystems:**

- **API client** (`lib/chatfs/api.py`): Wraps unofficial-claude-api, handles auth. See [docs/dev/technical-design/provider-interface.md].
- **Cache layer** (`lib/chatfs/cache.py`): Filesystem operations, mtime tracking, lazy creation (design TODO).
- **Plumbing tools** (`lib/chatfs/plumbing/`): JSONL-based modules for raw operations. See [docs/dev/technical-design.md#plumbing-tools].
- **Porcelain** (`lib/chatfs/porcelain/`, future): Human-friendly wrappers. See [docs/dev/technical-design/porcelain-layer.md].

## Data Flow

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

See [docs/dev/technical-design.md#data-flow] for details.

## Key Files

- `lib/chatfs/plumbing/` - JSONL-based modules (list_orgs, list_convos, get_convo, render_md)
- `lib/chatfs/api.py` - API client wrapper (wraps unofficial-claude-api)
- `lib/chatfs/cache.py` - Filesystem cache (design TODO)
- `lib/chatfs/models.py` - Data structures (Org, Conversation, Message)
- `docs/dev/` - Design documentation
- `design-incubators/fork-representation/` - Unsolved fork representation problem

## Conventions

**File naming:**

- Plumbing modules: `lib/chatfs/plumbing/verb_noun.py` (e.g., `list_orgs.py`)
- CLI commands (via packaging): `chatfs-verb-noun` (e.g., `chatfs-list-orgs`)
- Libraries: `lib/chatfs/noun.py` (e.g., `lib/chatfs/cache.py`)
- Design docs: `docs/dev/category/topic.md` (e.g., `docs/dev/technical-design/provider-interface.md`)

**JSONL format:**

- One JSON object per line
- UTF-8 encoding
- Streaming-friendly (process line-by-line)
- Works with jq: `chatfs-list-orgs | jq -r '.name'`

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
echo '{}' | chatfs-list-orgs | jq

# Test full pipeline
chatfs-list-orgs | head -n 1 | \
  chatfs-list-convos | head -n 5 | \
  chatfs-get-convo | \
  chatfs-render-md > output.md
```

See [HACKING.md#running-tests] for details.
