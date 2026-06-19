"""JSON loading with a real recursive type instead of `Any`.

The stdlib `json.loads` returns `Any`, which silently switches off type
checking for everything downstream. This module is the single place that
`Any` is allowed to exist: `loads` narrows the result to `JsonValue` — a
recursive union the type checker can follow — via a `TypeGuard`, so callers
get a checked value rather than `Any`.

The guard recurses through every node, so the narrowing reflects a value that
was actually walked and checked rather than asserted from the outside. The
`# pyright: ignore` lines are unavoidable: `isinstance` narrows `object` to
`list`/`dict` with *unknown* element types — exactly what the recursion exists
to pin down.
"""

import json
from typing import TypeGuard

type JsonPrimitive = None | bool | int | float | str
type JsonValue = JsonPrimitive | JsonArray | JsonObject
type JsonObject = dict[str, JsonValue]
type JsonArray = list[JsonValue]


def is_json_primitive(value: object) -> TypeGuard[JsonPrimitive]:
    return value is None or isinstance(value, (bool, int, float, str))


def is_json_array(value: object) -> TypeGuard[JsonArray]:
    return isinstance(value, list) and all(
        is_json_value(v)  # pyright: ignore[reportUnknownArgumentType]
        for v in value  # pyright: ignore[reportUnknownVariableType]
    )


def is_json_object(value: object) -> TypeGuard[JsonObject]:
    if not isinstance(value, dict):
        return False
    keys = all(
        isinstance(k, str)
        for k in value  # pyright: ignore[reportUnknownVariableType]
    )
    vals = all(
        is_json_value(v)  # pyright: ignore[reportUnknownArgumentType]
        for v in value.values()  # pyright: ignore[reportUnknownVariableType]
    )
    return keys and vals


def is_json_value(value: object) -> TypeGuard[JsonValue]:
    return is_json_primitive(value) or is_json_array(value) or is_json_object(value)


def loads(text: str) -> JsonValue:
    value: object = json.loads(text)  # pyright: ignore[reportAny]
    assert is_json_value(value), value
    return value
