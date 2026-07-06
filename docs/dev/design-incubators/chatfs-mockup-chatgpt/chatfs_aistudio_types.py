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

from typing import NotRequired, TypedDict, TypeGuard

from chatfs_json import JsonValue


class IndexItem(TypedDict):
    """A conversation's identity fields, synthesized from the JSPB doc.

    Only the fields layout reads are declared. Written verbatim to
    meta.json — but synthesized, not a verbatim service payload, since
    JSPB has no keyed object to pass through.
    """

    id: str  # Drive prompt id, `prompts/` prefix stripped
    title: str
    create_time: int  # unix seconds, from the first chunk's createTime


class Turn(TypedDict):
    """One entry in `prompt.chunkedPrompt.chunks[]`.

    Only the fields splat/layout read are declared; pass-through fields
    (grounding, tokenCount, thinkingLevel, …) ride along in the .json
    output untyped.
    """

    role: str  # "user" | "model"
    text: str
    createTime: tuple[str, int]  # [seconds-string, nanos] pair
    isThought: NotRequired[int]  # 1 when present; absent otherwise
    finishReason: NotRequired[int]  # 1 == STOP, present on completed model turns


class Metadata(TypedDict):
    displayName: str


class ChunkedPrompt(TypedDict):
    chunks: list[Turn]


class Prompt(TypedDict):
    name: str  # "prompts/<id>"
    metadata: Metadata
    chunkedPrompt: ChunkedPrompt


class Conversation(TypedDict):
    """The massaged conversation.json payload — chatfs_aistudio_conversation_massage_json's output."""

    prompt: Prompt


def is_turn(value: JsonValue) -> TypeGuard[Turn]:
    return (
        isinstance(value, dict)
        and isinstance(value.get("role"), str)
        and isinstance(value.get("text"), str)
    )


def is_conversation(value: JsonValue) -> TypeGuard[Conversation]:
    if not isinstance(value, dict):
        return False
    prompt = value.get("prompt")
    if not isinstance(prompt, dict) or not isinstance(prompt.get("name"), str):
        return False
    metadata = prompt.get("metadata")
    chunked_prompt = prompt.get("chunkedPrompt")
    if not isinstance(metadata, dict) or not isinstance(chunked_prompt, dict):
        return False
    if not isinstance(metadata.get("displayName"), str):
        return False
    chunks = chunked_prompt.get("chunks")
    return isinstance(chunks, list) and all(is_turn(c) for c in chunks)
