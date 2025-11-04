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

chatfs provides lazy filesystem access to chat conversations (claude.ai, ChatGPT). Built on four-layer architecture: native → vfs → cache → cli.

**Why JSONL:** Streaming-friendly, works with Unix tools now, easy capnproto migration later.

**Four layers:**

- **M1-CLAUDE** (`lib/chatfs/layer/native/claude/`): Direct Claude API wrapper, outputs raw JSONL. See [docs/dev/technical-design/provider-interface.md].
- **M2-VFS** (`lib/chatfs/layer/vfs/`): Normalized JSONL across providers (Claude, ChatGPT). See [docs/dev/technical-design.md#m2-vfs-layer].
- **M3-CACHE** (`lib/chatfs/layer/cache/`): Persistent storage with staleness tracking (future). See [docs/dev/technical-design.md#m3-cache-layer].
- **M4-CLI** (`lib/chatfs/layer/cli/`, future): Human-friendly commands with colors, progress bars. See [docs/dev/technical-design/cli-layer.md].

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

- `lib/chatfs/layer/native/claude/` - M1-CLAUDE: Claude-native commands (list_orgs, list_convos, get_convo, render_md)
- `lib/chatfs/layer/vfs/` - M2-VFS: Normalized JSONL commands (future)
- `lib/chatfs/layer/cache/` - M3-CACHE: Persistent storage layer (future)
- `lib/chatfs/layer/cli/` - M4-CLI: Human-friendly commands (future)
- `lib/chatfs/client.py` - API client wrapper (wraps unofficial-claude-api)
- `lib/chatfs/models.py` - Data structures (Org, Conversation, Message)
- `docs/dev/` - Design documentation
- `design-incubators/fork-representation/` - Fork representation investigation

## Conventions

**File naming:**

- Native modules: `lib/chatfs/layer/native/claude/verb_noun.py` (e.g., `list_orgs.py`)
- VFS modules: `lib/chatfs/layer/vfs/verb_noun.py` (e.g., `list_orgs.py`)
- CLI commands (via packaging):
  - M1-CLAUDE: `chatfs-claude-verb-noun` (e.g., `chatfs-claude-list-orgs`)
  - M2-VFS: `chatfs-vfs-verb-noun` (e.g., `chatfs-vfs-list-orgs`)
  - M3-CACHE: `chatfs-cache-verb-noun` (e.g., `chatfs-cache-list-orgs`)
  - M4-CLI: `chatfs <subcommand>` (e.g., `chatfs ls`, `chatfs cat`)
- Libraries: `lib/chatfs/noun.py` (e.g., `lib/chatfs/client.py`)
- Design docs: `docs/dev/category/topic.md` (e.g., `docs/dev/technical-design/provider-interface.md`)

**JSONL format:**

- One JSON object per line
- UTF-8 encoding
- Streaming-friendly (process line-by-line)
- Works with jq: `chatfs-list-orgs | jq -r '.name'`

**JSONL layer contract (M1-CLAUDE, M2-VFS, M3-CACHE):**

- Read JSONL from stdin
- Write JSONL to stdout (except render-md → markdown)
- Log errors to stderr
- Exit 0 on success
- No terminal dependencies (colors, progress bars)

**CLI layer contract (M4-CLI):**

- Path-based interface (not JSONL)
- May use colors, progress bars, interactive prompts
- Output for human consumption

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
