# Unrecognized shape degrades visibly, never crashes

The render-layer counterpart to
`zero-data-loss-is-the-correctness-target.md`: that policy says capture
fails loudly on its own invariants but a consumer may filter on read.
This resolves what "filter on read" means when the render/splat layer
meets a third-party shape it doesn't recognize — a claude content block
type, a chatgpt `content_type`, an AI Studio turn that's neither thought
nor answer, any future provider's equivalent.

The rule: never crash the whole conversation's render over one
unrecognized fragment, and never drop it silently either. Render it
in-band, verbatim, visibly — a `<details type="unmodeled">` disclosure
carrying the raw JSON — and warn on stderr. Both halves matter:

- **Never crash.** The wire format is a third party's and unversioned
  (see `opaque-extractor-boundary.md` — there is no spec to consult, so
  exhaustive case-modeling ahead of time is a losing race). A fresh
  shape is expected drift, not a bug, and losing an entire capture's
  render over one unfamiliar fragment is a worse failure than showing
  that fragment badly.
- **Never hide.** A silently-dropped fragment is unrecoverable the
  moment the render is treated as complete. Passthrough keeps the raw
  data on the page, so re-rendering later — once schema knowledge
  catches up — recovers full fidelity from what's already there. This
  makes the render a durable record, not just a stopgap: today's
  `<details type="unmodeled">` block is tomorrow's backfill input.

## No runtime lax/strict flag

The alternative this rejects: a mode switch that raises in "strict" and
warns in "lax". That's two code paths to trust and test, and a real
risk of running in the wrong mode at the wrong time (strict against
live user data, lax while trying to catch drift in CI). A single
uniform behavior — always degrade, never hide, never crash — has
neither failure mode.

Drift detection moves to tests instead of a runtime flag: assert a
golden fixture corpus renders with zero `type="unmodeled"` markers
(`grep -L 'type="unmodeled"'` across known-good captures). That's a
test concern, decoupled from runtime behavior that must never crash on
real user data.

## What still raises

`raise`/`assert` stays reserved for violations of the tool's *own*
invariants — a bug in our code, not a surprise in someone else's wire
format. Example: AI Studio's `render.py::parse_stem` asserting our own
generated filename shape (`{index}.{role}[.note]`) is a self-consistency
check, not a third-party-data check, and correctly still raises.

## Manifestations (2026-08-16)

Converted from raise to passthrough-plus-warn:

- `claude/conversation/splat.py::extract_text` — unrecognized content
  block type, and a `tool_result` with no preceding `tool_use` in the
  same message (rendered via the existing `render_tool_result`, since
  the shape is known even though the position is unexpected).
- `chatgpt/conversation/splat.py::extract_text_content` — unrecognized
  `content_type`.
- `aistudio/conversation/splat.py::turn_kind` — a model turn that's
  neither `thought` nor `answer`, and a turn role that's neither `user`
  nor `model`.
