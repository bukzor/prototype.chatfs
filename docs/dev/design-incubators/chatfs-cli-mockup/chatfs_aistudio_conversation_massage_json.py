#!/usr/bin/env python3
"""Massage an AI Studio prompt's raw JSPB into a named JSON conversation doc.

chatgpt and claude don't need this: their wire format is already keyed JSON,
so their `conversation.json` is the raw API response, verbatim. AI Studio's
is JSPB (positional arrays) — a stage has to assign names before the result
is "good" json, i.e. the same shape of thing chatgpt/claude get for free.

Input (stdin): conversation.json.d/raw.json — one plucked prompt message (a
JSPB array; chatfs_aistudio_layout.pluck_conversation already unwraps the
ResolveDriveResource envelope). Plucking (picking this body out of the CDP
capture) is a separate, earlier step; this script does not re-narrow the
result to any subset (e.g. just turns) — it emits the whole named document,
mirroring what chatgpt/claude already have whole.

Output (stdout): conversation.json — the complete named projection, not a
partial guess: per design.kb/040-design.kb/no-partial-synthesis.md, a schema
must be written whole or not at all. SCHEMA below only omits slots nobody has
reverse-engineered yet (they stay dropped, same as any other null slot).

SCHEMA is ported from ../aistudio-schema/rosetta/convert.py (not imported —
that package is exploratory/disposable), where it's cross-checked against a
live `?alt=json` response for the same prompt (see that package's
verify.py). Field numbers additionally cross-checked against
dev.kb/claims.kb/aistudio-jspb-prompt-shape.md and chatfs_aistudio_layout.py /
chatfs_aistudio_conversation_splat.py, which index this same payload by hand.

A field spec is one of:
    "name"            scalar (or scalar list): emit the value unchanged
    ("name", {...})   nested message: recurse with the given sub-schema
    ("name", [{...}]) repeated message: map each element with the sub-schema
    ("name", "map")   repeated [key, value] pairs: fold into an object
"""
import json
import sys
from collections.abc import Mapping, Sequence
from typing import Literal, TypeAlias

import chatfs_json
from chatfs_json import JsonObject, JsonValue, is_json_array

Schema: TypeAlias = Mapping[int, "Field"]
Field: TypeAlias = (
    str
    | tuple[str, "Schema"]
    | tuple[str, "Sequence[Schema]"]
    | tuple[str, Literal["map"]]
)

USER: Schema = {0: "displayName", 1: "isMe", 2: "photoUri"}

LAST_MODIFIED: Schema = {0: "revisionTime", 1: ("user", USER)}

CAPABILITIES: Schema = {0: "canEdit", 1: "canShare", 2: "canCopy"}

METADATA: Schema = {
    0: "displayName",
    2: ("owner", USER),
    4: ("lastModified", LAST_MODIFIED),
    5: ("capabilities", CAPABILITIES),
    10: ("multimodalAttributes", {}),
    11: ("customProperties", "map"),
}

SAFETY_SETTING: Schema = {2: "category", 3: "threshold"}

RUN_SETTINGS: Schema = {
    0: "temperature",
    2: "model",
    4: "topP",
    5: "topK",
    6: "maxOutputTokens",
    7: ("safetySettings", [SAFETY_SETTING]),
    9: "enableCodeExecution",
    14: "enableSearchAsATool",
    17: "enableBrowseAsATool",
    18: "enableAutoFunctionResponse",
    24: "thinkingBudget",
    25: ("googleSearch", {}),
    28: "thinkingLevel",
    30: "enableImageSearch",
    31: "enableGoogleMaps",
    32: "enableAgentThinkingSummariesControl",
    33: "enableAgentVisualizationControl",
    34: "enableAgentCollaborativePlanningControl",
}

CORROBORATION_SEGMENT: Schema = {0: "index", 1: "uri", 2: "footnoteNumber"}

GROUNDING_SOURCE: Schema = {0: "referenceNumber", 1: "uri", 2: "title"}

GROUNDING: Schema = {
    0: ("corroborationSegments", [CORROBORATION_SEGMENT]),
    1: "webSearchQueries",
    2: ("groundingSources", [GROUNDING_SOURCE]),
}

PART: Schema = {1: "text", 12: "thought", 14: "thoughtSignature"}

CHUNK: Schema = {
    0: "text",
    8: "role",
    15: ("grounding", GROUNDING),
    16: "finishReason",
    18: "tokenCount",
    19: "isThought",
    28: "errorMessage",
    29: ("parts", [PART]),
    30: "thinkingLevel",
    31: "isGeneratedUsingApiKey",
    32: "createTime",
    35: "aspectRatio",
}

CHUNKED_PROMPT: Schema = {0: ("chunks", [CHUNK]), 1: ("pendingInputs", [CHUNK])}

PROMPT: Schema = {
    0: "name",
    3: ("runSettings", RUN_SETTINGS),
    4: ("metadata", METADATA),
    12: ("systemInstruction", {}),
    13: ("chunkedPrompt", CHUNKED_PROMPT),
}


def from_message(values: JsonValue, schema: Schema) -> JsonObject:
    """Project a positional message onto its named fields, dropping null slots."""
    assert is_json_array(values), values
    out: JsonObject = {}
    for slot, spec in schema.items():
        if slot >= len(values) or values[slot] is None:
            continue
        out_key, value = name_and_value(spec, values[slot])
        out[out_key] = value
    return out


def name_and_value(spec: Field, value: JsonValue) -> tuple[str, JsonValue]:
    match spec:
        case str(name):
            return name, value
        case (name, dict() as sub):
            return name, from_message(value, sub)
        case (name, [sub]):
            assert is_json_array(value), value
            return name, [from_message(elem, sub) for elem in value]
        case (name, "map"):
            return name, fold_map(value)
        case _:
            raise AssertionError(spec)


def fold_map(pairs: JsonValue) -> JsonObject:
    """Fold a jspb map field — repeated [key, value] pairs — into an object."""
    assert is_json_array(pairs), pairs
    out: JsonObject = {}
    for pair in pairs:
        assert is_json_array(pair) and len(pair) == 2, pair
        key, value = pair
        assert isinstance(key, str), key
        out[key] = value
    return out


def massage(doc: JsonValue) -> JsonObject:
    """Project one plucked prompt message onto the named PROMPT schema.

    Wrapped in a `prompt` key to match the real named API response shape
    (verified against aistudio-schema/rosetta/resolvedrive.alt-json.json,
    whose top-level key is `prompt`) — not an arbitrary envelope choice.
    """
    return {"prompt": from_message(doc, PROMPT)}


def main() -> None:
    doc = chatfs_json.loads(sys.stdin.read())
    conversation = massage(doc)
    json.dump(conversation, sys.stdout, ensure_ascii=False, indent=2)
    _ = sys.stdout.write("\n")


if __name__ == "__main__":
    main()
