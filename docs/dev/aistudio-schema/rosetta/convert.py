#!/usr/bin/env python3
"""Convert AI Studio's positional jspb dump into its named-JSON form.

AI Studio serializes each subject two ways: a named JSON object, and a `jspb`
array where every protobuf field sits at a fixed slot. Null/absent slots have
no named counterpart, so the named form is sparse.

Every endpoint under `endpoint/<name>/` is HYPOTHESIZED to share the same
PROMPT/METADATA message types — one SCHEMA below. That hypothesis is not
settled here; it's what `verify.py` keeps testing, per endpoint, against each
endpoint's real alt=json golden pair (see `../discourse.kb/questions.kb/
can-we-decode-deterministically.md` for current status — open, not confirmed).
Only the top-level wrapper shape is declared to differ per endpoint (singular
vs. repeated, and the wrapper key), via that endpoint's own `meta.json`
(`top_level_key`, `repeated`) rather than baked in here. A future endpoint
whose golden pair diverges under this one SCHEMA is evidence against the
hypothesis, not a bug in this converter.

This converter is driven by SCHEMA: a sparse `slot -> field` map per message
type. We name only the slots we've identified; unknown and null slots are
dropped. Values are passed through verbatim — booleans stay `0`/`1`, enums stay
ints, and timestamps stay `[seconds, nanos]`, exactly as jspb encodes them.

A field spec is one of:
    "name"            scalar (or scalar list): emit the value unchanged
    ("name", {...})   nested message: recurse with the given sub-schema
    ("name", [{...}]) repeated message: map each element with the sub-schema
    ("name", "map")   repeated [key, value] pairs: fold into an object
"""

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import IO, Literal, TypeAlias, TypeGuard

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


def is_sequence(o: object) -> TypeGuard[Sequence[object]]:
    """Narrow a decoded-JSON value to a positional array (a jspb message/list).

    Excludes str/bytes: a scalar string is a Sequence but never a message.
    """
    return isinstance(o, Sequence) and not isinstance(o, (str, bytes))


def is_mapping(o: object) -> TypeGuard[Mapping[str, object]]:
    """Narrow a decoded-JSON value to an object — JSON keys are always strings."""
    return isinstance(o, Mapping)


def from_message(values: object, schema: Schema) -> dict[str, object]:
    """Project a positional message onto its named fields, dropping null slots."""
    assert is_sequence(values), values
    out: dict[str, object] = {}
    for slot, spec in schema.items():
        if slot >= len(values) or values[slot] is None:
            continue
        out_key, value = name_and_value(spec, values[slot])
        out[out_key] = value
    return out


def name_and_value(spec: Field, value: object) -> tuple[str, object]:
    match spec:
        case str(name):
            return name, value
        case (name, dict() as sub):
            return name, from_message(value, sub)
        case (name, [sub]):
            assert is_sequence(value), value
            return name, [from_message(elem, sub) for elem in value]
        case (name, "map"):
            return name, fold_map(value)
        case _:
            raise AssertionError(spec)


def fold_map(pairs: object) -> dict[object, object]:
    """Fold a jspb map field — repeated [key, value] pairs — into an object."""
    assert is_sequence(pairs), pairs
    out: dict[object, object] = {}
    for pair in pairs:
        assert is_sequence(pair) and len(pair) == 2, pair
        key, value = pair
        out[key] = value
    return out


def from_jspb(jspb: object, meta: Mapping[str, object]) -> dict[str, object]:
    """Top-level: unwrap per the endpoint's meta.json.

    `top_level_key` names the wrapper field; `repeated` picks singular
    (`{key: <msg>}`, e.g. resolvedrive's one prompt) vs. repeated
    (`{key: [<msg>, ...]}`, e.g. listprompts' page of prompts).
    """
    assert is_sequence(jspb), jspb
    key = meta["top_level_key"]
    assert isinstance(key, str), meta
    if meta["repeated"]:
        prompts = jspb[0]
        assert is_sequence(prompts), prompts
        return {key: [from_message(p, PROMPT) for p in prompts]}
    return {key: from_message(jspb[0], PROMPT)}


def load_json(fp: IO[str]) -> object:
    """json.load retyped Any -> object — the lone suppression for stdlib's Any.

    Callers narrow the result themselves (is_sequence) before using it.
    """
    return json.load(fp)  # pyright: ignore[reportAny]


def load_meta(endpoint_dir: Path) -> Mapping[str, object]:
    """Load `ENDPOINT_DIR/meta.json` — the endpoint-specific config every
    rosetta/ script reads: `top_level_key`/`repeated` (this module),
    `method`/`default_param`/`body` (capture.sh)."""
    with open(endpoint_dir / "meta.json") as fp:
        meta = load_json(fp)
    assert is_mapping(meta), meta
    return meta


def main():
    import sys

    argv = sys.argv[1:]
    if len(argv) != 1:
        raise SystemExit("usage: convert.py ENDPOINT_DIR < jspb.json")
    meta = load_meta(Path(argv[0]))

    jspb = load_json(sys.stdin)
    json.dump(from_jspb(jspb, meta), sys.stdout, ensure_ascii=False, indent=2)
    _ = sys.stdout.write("\n")


if __name__ == "__main__":
    main()
