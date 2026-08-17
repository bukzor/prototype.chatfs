"""Shared per-message splat-stage rendering, factored out of the three
provider splats (`chatfs.provider.{claude,chatgpt,aistudio}.conversation
.splat`), which had each grown byte-for-byte copies.

`fenced_json`/`render_details` render one raw message/turn's non-answer
content (tool calls, reasoning, unmodeled shapes) into a markdown
fragment; `chatfs.render` (a different stage) assembles those fragments'
*outputs* -- the per-message .md files -- into the whole conversation
tree. Not the same module: splat-stage fragment rendering is
provider-facing raw-content-in, render-stage assembly is
Turn/ConversationTree-in.
"""

import json
from decimal import Decimal


def _json_default(obj: object) -> object:
    """`json.dumps(default=...)` hook for values `fenced_json` can't
    otherwise serialize -- chiefly `Decimal`, which chatgpt's
    Decimal-preserving JSON parse can put anywhere in a raw content dict."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def fenced_json(value: object) -> str:
    """Render `value` as a fenced ```json code block, for a raw dump inside
    a `render_details` disclosure."""
    return "```json\n" + json.dumps(value, indent=2, ensure_ascii=False, default=_json_default) + "\n```"


def render_details(kind: str, icon: str, label: str, body: str, tool: str | None = None) -> str:
    """Wrap non-answer content in a collapsible `<details>`, tagged for grep.

    `type="{kind}"` makes each block kind searchable across every provider
    (`grep 'type="thinking"'`, `grep 'type="tool_call"'`); `tool="{tool}"`
    further distinguishes tool calls by name. `<details>` (vs a blockquote)
    keeps the content collapsed-by-default and avoids colliding with the
    render step's blockquote-as-fork-depth convention.
    """
    tool_attr = f' tool="{tool}"' if tool else ""
    return (
        f'<details type="{kind}"{tool_attr}><summary>{icon} {label}</summary>'
        f"\n\n{body}\n\n</details>"
    )
