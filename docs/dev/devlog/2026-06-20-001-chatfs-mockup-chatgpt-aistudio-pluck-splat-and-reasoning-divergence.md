# 2026-06-20: chatfs-mockup-chatgpt — AI Studio pluck + splat, and the cross-provider reasoning divergence

## Focus

Stand up the first AI Studio provider rungs (pluck + splat) from a single
captured prompt, matching the chatgpt/claude pipeline shape. Then review both,
and answer whether the thoughts↔turns mapping is consistent across providers.

## What Happened

**The conversation lives in one `ResolveDriveResource` RPC body** (line 426 of
`aistudio.har.jsonl`), mime `application/json+protobuf` — JSPB, i.e. **positional
arrays, not keyed objects**. That single body carries the whole prompt; one
captured conversation → one doc, same as the chatgpt/claude pluck. The endpoint
is generic (index/recents reuse it), so the pluck guards on body shape
(`[0][0] == "prompts/<id>"`) rather than URL alone.

**Reverse-engineered the JSPB field map** (recorded in
`dev.kb/claims.kb/aistudio-jspb-prompt-shape.md`): turns at `[0][13][0]`; each
36-field turn has text at `[0]`, role at `[8]`, answer flag `[16]`, thought flag
`[19]`. `[0][13]` is a `[live_turns, draft]` pair — the splat takes `[0]` and
ignores the empty `[1]` draft turn (which would otherwise emit a 16th blank turn).

**The splat fans the one doc into per-turn files** —
`messages/NNN.{role}[.thought].{json,md}`, zero-padded index for sort order
(JSPB has no per-turn id/timestamp). Thoughts render as
`<details type="thinking">`, matching the claude side's grep contract; the
leading `**bold**` header is lifted into `<summary>` and stripped from the body
only when the first line is exactly that header.

**Key finding — reasoning maps to turns three different ways:**

- **claude** nests `thinking` as a block *inside* the assistant message's
  `content[]` (intra-turn).
- **chatgpt** externalizes it as separate `mapping` nodes (`content_type:
  "thoughts"` *plus* a distinct `reasoning_recap`), many-per-response.
- **aistudio** externalizes it as separate *turns* (`[19]==1`), 1:1 with the
  answer in this capture (not guaranteed).

This exposed a real design gap: the canonical conversation graph
(`message_id/parent_id/author/content/timestamp`) has **no reasoning slot**, so
where thinking lands is a per-parser decision and a uniform "one response = one
unit" view must be synthesized in BB2/BB3. Captured as two claims plus a note on
the project-level `040-design.kb/canonical-conversation-graph.md`.

## State / Follow-ups

Pluck + splat landed and verified (15 turns from the test prompt). Remaining
ladder rungs (index, render, orchestrators, browse automation) tracked in
`.claude/todo.kb/2026-06-20-000-aistudio-provider-parity-ladder.md`. All field
indices are `status: observed` from one capture — a prompt with images, multiple
parts, or a fork could refute the 36-field width or the 1:1 thought↔answer ratio.

AI Studio is a third *browser-captured* provider, which strengthens the
shared-lib extraction signal earlier than the claude-code trigger assumed in
`2026-05-11-001-shared-code-among-providers.md`.
