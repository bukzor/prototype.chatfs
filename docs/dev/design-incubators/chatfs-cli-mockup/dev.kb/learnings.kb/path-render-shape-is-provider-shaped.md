# `path_render` shape is provider-shaped, not provider-specific

After mirroring `chatfs_chatgpt_conversation_path_render.py` to the
claude side, the only real variation is **how the splat helper is
invoked**:

- chatgpt: `chatgpt-splat` (PATH console script wrapping
  `bukzor.chatgpt_export.splat`)
- claude: `chatfs_claude_conversation_splat.py` (sibling .py invoked
  via `Path(__file__).parent`)

Everything else — `purge_non_captured` allowlist `{".data"}`, the
move-from-splat loop, the render hand-off — survived byte-identical.

A third provider confirms it: `chatfs_aistudio_conversation_path_render.py`
(landed 2026-07-11) invokes splat the claude way (sibling `.py`) and is
otherwise byte-for-byte the same shape too — despite AI Studio's wire
format and render tree both being genuinely different from claude's
(JSPB vs. keyed JSON; a fork-less chain vs. a real tree). The orchestrator
shape is invariant to both of those differences.

## Implication for the eventual lib

When the parity ladder reaches the lib-extraction rung, `path_render`
is a strong candidate for the shared core. The per-provider piece
reduces to a one-line "how to invoke splat". The `$PATH` vs sibling
distinction is itself an accident of history (chatgpt had a pre-
existing console script, claude was written from scratch); the lib
could normalize on one convention.

## See also

- Project-level strategic todo `shared code among providers`.
- Devlogs `2026-05-11-001-…-claude-mvp-closed.md` and
  `2026-05-12-000-…-claude-entry-point-parity.md`.
