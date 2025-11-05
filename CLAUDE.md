# chatfs - Development Guide for Claude

**Last Updated:** 2025-11-01

## Quick Reference

**Testing JSONL layer commands** (commands available after M0-DOCS configures entry points):

**M1-CLAUDE commands** (`native/claude` layer, outputs raw API data):
```bash
echo '{}' | chatfs-claude-list-orgs | jq
echo '{"uuid":"org-uuid"}' | chatfs-claude-list-convos | jq
echo '{"uuid":"convo-uuid"}' | chatfs-claude-get-convo | jq
echo '{}' | chatfs-claude-list-orgs | head -n1 | chatfs-claude-list-convos | head -n1 | chatfs-claude-get-convo | chatfs-claude-render-md
```

For newly added JSONL commands, use `uv sync` to install.
Use echo + pipe + jq. Example: `echo '{"uuid":"abc"}' | chatfs-claude-list-convos | jq`. See [HACKING.md#running-tests].

**Working with unofficial API:**
Wrapped in `lib/chatfs/client.py`. Uses curl_cffi for Cloudflare bypass. Raw access: `from unofficial_claude_api import Client`. See [docs/dev/technical-design/provider-interface.md].

**Current state:** See [STATUS.md] for milestone, blockers, and next actions. Recent devlogs: [docs/dev/devlog/].

## Architecture Overview

chatfs provides lazy filesystem access to chat conversations (claude.ai, ChatGPT). Built on four-layer architecture: native → vfs → cache → cli.

**Why JSONL:** Streaming-friendly, works with Unix tools now, easy capnproto migration later.

**Important terminology notes:**

- **M0-DOCS, M1-CLAUDE, M2-VFS, M3-CACHE, M4-CLI are milestone names** (not layer names). They happen to align with layer names for the first four milestones, but this is coincidental. Milestones will be completed and removed from the codebase.

**Four layers (implemented across milestones):**

- **native** - Provider-specific API wrappers (`lib/chatfs/layer/native/*/`):
  - `native/claude` (M1-CLAUDE): Direct claude.ai API wrapper, outputs raw JSONL. See [docs/dev/technical-design/provider-interface.md].
  - `native/chatgpt` (future): ChatGPT API wrapper
  - `native/gemini` (future): Gemini API wrapper
- **vfs** (`lib/chatfs/layer/vfs/`, milestone M2-VFS): Normalized JSONL across providers. See [docs/dev/technical-design.md#vfs-layer].
- **cache** (`lib/chatfs/layer/cache/`, milestone M3-CACHE): Persistent storage with staleness tracking (future). See [docs/dev/technical-design.md#cache-layer].
- **cli** (`lib/chatfs/layer/cli/`, milestone M4-CLI, future): Human-friendly commands with colors, progress bars. See [docs/dev/technical-design/cli-layer.md].

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

## Working on Documentation

**Documentation editing principles:**

- **80% confidence threshold** - Make edits when reasonably confident. Do NOT over-hedge or seek permission for routine edits. Edit first, discuss if uncertain.
- **Discussion over speculation** - When uncertain about concepts or design decisions, discuss with user to develop understanding before writing. Don't guess.
- **Breadth-first validation** - Review higher-level docs before diving into subdocs. Subdocs may not be needed if main doc covers it well.

**Documentation workflows:**

General validation workflow:
1. **Discuss** concepts with user to develop deep understanding
2. **Read** existing content
3. **Evaluate** accuracy/completeness
4. **Correct/Rewrite** with confidence

NOT: Mechanical fill-in-the-blanks. Reach certainty before making changes.

**Handling TODO-marked docs:**

When you encounter docs marked with "Status: TODO":
1. **Never fill in TODO docs solo** - These require discussion with user first
2. **Discuss concepts first** - Develop understanding through conversation
3. **Only write after reaching certainty** - Discussion must establish clear understanding
4. **May prove unnecessary** - Some breakdown docs might be deleted if main doc suffices

**Subdoc creation policy:**
- Only create subdocs when >100-200 lines or frequently referenced independently
- Otherwise keep content in main doc
- See [docs/dev/documentation-howto.md] for full guidelines

**Deferring implementation details:**
- Clearly mark what's intentionally deferred to implementation phases
- Mark as "TBD in M1-CLAUDE" or similar (not empty TODO stubs)
- Avoid creating placeholder docs that add no value
- Discuss what level of detail is appropriate for design phase vs implementation phase

**Where documentation topics live:**

| Topic Layer                  | Doc Location                                             |
| ---------------------------- | -------------------------------------------------------- |
| L0: Project concept          | README.md                                                |
| L1: Problem Space            | design-rationale.md (intro)                              |
| L1: Design Philosophy        | design-rationale.md (core decisions)                     |
| L1: Architecture             | technical-design.md#architecture                         |
| L1: Open Questions           | design-incubators/                                       |
| L2: Rationale details        | design-rationale/*.md                                    |
| L2: Architecture elaboration | technical-design.md (sections)                           |
| L2: Data Formats             | technical-design/*.md                                    |
| L3: Component interfaces     | technical-design/*.md subdocs                            |
| L4: Implementation specifics | technical-design/*.md OR development-plan/milestone-*.md |

## Key Files

- `lib/chatfs/layer/native/claude/` - M1-CLAUDE: Claude-native commands (list_orgs, list_convos, get_convo, render_md)
- `lib/chatfs/layer/vfs/` - M2-VFS: Normalized JSONL commands (future)
- `lib/chatfs/layer/cache/` - M3-CACHE: Persistent storage layer (future)
- `lib/chatfs/layer/cli/` - M4-CLI: Human-friendly commands (future)
- `lib/chatfs/client.py` - API client wrapper (wraps unofficial-claude-api)
- `lib/chatfs/models.py` - Data structures (Org, Conversation, Message)
- `docs/dev/` - Design documentation
- `docs/dev/design-incubators/fork-representation/` - Fork representation investigation

## Conventions

**File naming:**

- Native modules: `lib/chatfs/layer/native/claude/verb_noun.py` (e.g., `list_orgs.py`)
- VFS modules: `lib/chatfs/layer/vfs/verb_noun.py` (e.g., `list_orgs.py`)
- CLI commands (via packaging):
  - M1-CLAUDE: `chatfs-claude-verb-noun` (e.g., `chatfs-claude-list-orgs`)
  - M2-VFS: `chatfs-vfs-verb-noun` (e.g., `chatfs-vfs-list-orgs`)
  - M3-CACHE: `chatfs-cache-verb-noun` (e.g., `chatfs-cache-list-orgs`)
  - M4-CLI: `chatfs-ls`, `chatfs-cat`, etc. (future: `chatfs <subcommand>` as optional enhancement)
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
