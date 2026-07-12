---
why:
  - provider-agnostic-interface
---

# Provider Plugin Model — Lessons from Three Providers

The parent `docs/dev/design.kb/040-design.kb/provider-plugin-model.md`
states the abstract shape (a provider defines locator parsing, artifact
placement, BB1/BB2/BB3 invocation, staleness, mount layout). This entry
records what building chatgpt, claude, and AI Studio side by side actually
showed about where the provider/universal boundary falls — the extraction
landed 2026-07-05 as `chatfs_layout.py` + `chatfs_render.py`.

## The three-way split

**Byte-for-byte identical across all three** (→ `chatfs_layout.py`):
`safe_filename`, `_iso_offset`, `time_dir_for`, `chat_dir_for`,
`data_dir_for`, `resolve_chat_dir`, `_purge_view_symlinks`,
`DATA_DIR_NAME`, and the body of `place_meta` (meta.json write +
view-symlink placement). Same story on the render side:
`chatfs_render.py`'s tree algorithms (`live_ancestors`, `primary_child`,
`normalize_turnless`, `number_turns`, the fork-fact `Renderer`) are one
shared implementation; `chatfs_chatgpt_conversation_render.py`,
`chatfs_claude_conversation_render.py`, and (landed 2026-07-11)
`chatfs_aistudio_conversation_render.py` contribute only wire-shape
parsing. AI Studio's contribution is the strongest evidence yet that the
render-side seam is right: its wire shape has *no fork representation at
all* (a flat, linear turn list — see
`dev.kb/claims.kb/aistudio-jspb-prompt-shape.md`), so its renderer feeds
`render_tree` a degenerate single-child-chain tree; the shared fork-fact
machinery costs nothing on that input rather than needing a
provider-specific bypass.

**Provider-shaped, but collapses to a fixed small adapter** — not a
free-form interface, a **3-value tuple** (`id`, `title`,
`created: datetime`) plus one parser:

```python
def _created(raw) -> datetime: ...      # provider's own timestamp shape
def place_meta(item, root) -> Path:
    return _place_meta(item[id_key], item[title_key], _created(item[time_key]), item, root)
```

Every provider's `place_meta` wrapper is this shape, verified identical in
structure across `chatfs_{chatgpt,claude,aistudio}_layout.py` — only the
key names (`id`/`title`/`create_time` vs `uuid`/`name`/`created_at` vs
`id`/`title`/`create_time`) and the timestamp parser's input type
(str | float vs str vs int) differ. This one seam absorbs both the
key-name divergence and the timestamp-type divergence; nothing else
about `place_meta` varies.

`capture()` (landed shared 2026-07-11, see
`../../.claude/todo.kb/2026-07-03-000-cross-provider-data-flow-drift--pre-unification-fixes-vs-unification-scope.md`
§ "Solve by unification") turned out to be the same adapter shape, one
level simpler — a 2-value tuple (`pluck_script`,
`conversation_filename`) instead of a 3-value tuple plus parser, since
browse+pluck orchestration itself has no provider-shaped logic at all,
only provider-shaped *inputs*:

```python
def capture(url, chat_dir) -> Path:
    return _capture(url, chat_dir, CONVERSATION_PLUCK)  # + conversation_filename= for aistudio
```

**Genuinely provider-only** (stays out of the shared lib entirely):
- AI Studio's `index_item()` — synthesizes an `IndexItem` from positional
  JSPB, since JSPB has no native keyed dict to echo (chatgpt/claude get
  `IndexItem` for free from their already-keyed wire format).
- Each provider's extractor (HAR-pluck, CDP+pluck, JSONL-read) and content
  splat — genuinely different wire formats, the opaque-extractor boundary
  (`../../../../technical-policy.kb/`) puts these out of scope for sharing
  by design, not by omission.

## Revised rule-of-three take

The pre-registration in
`../../.claude/todo.kb/2026-05-11-001-shared-code-among-providers.md`
expected claude-code (a fourth, non-browser provider) to be the extraction
trigger. AI Studio — a third *browser-captured* provider, but the first
non-keyed (JSPB) one — turned out to be sufficient signal on its own: the
keyed-vs-positional split stress-tested the adapter shape more than a
fourth keyed provider would have.
