"""Shared types for the AI Studio mockup.

Unlike chatgpt and claude, AI Studio's source is JSPB (positional
arrays, not keyed objects), so there is no native conversation-item
dict to pass through. `IndexItem` is therefore *synthesized* from
positional fields — the keys are ours, not the service's (see
`chatfs_aistudio_layout.index_item`).

The synthesized shape echoes the chatgpt one (id/title/create_time) —
the outlier is claude (uuid/name/created_at, ISO string). But the echo
isn't free: AI Studio's created field arrives as a numeric *string*,
coerced to int here, where chatgpt's is already numeric. That two of
three providers nearly share this shape is the load-bearing signal for
the shared-layout boundary.
"""

from typing import TypedDict


class IndexItem(TypedDict):
    """A conversation's identity fields, synthesized from the JSPB doc.

    Only the fields layout reads are declared. Written verbatim to
    meta.json — but synthesized, not a verbatim service payload, since
    JSPB has no keyed object to pass through.
    """

    id: str  # Drive prompt id, `prompts/` prefix stripped
    title: str
    create_time: int  # unix seconds, from the first chunk's createTime
