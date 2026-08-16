"""Decimal-preserving JSON, for chatgpt's sub-millisecond message timestamps.

`typed_json` (used everywhere else in chatfs) parses floats as `float`,
which loses precision on chatgpt's `create_time` (nanosecond-fraction unix
timestamps -- more significant digits than float64 carries). This module
parses floats as `Decimal` instead, so `splat.format_timestamp` can render
the fractional part losslessly.
"""

from collections.abc import Mapping
from decimal import Decimal
from typing import IO, cast

type JsonValue = None | bool | int | Decimal | str | list[JsonValue] | JsonObj
type JsonObj = Mapping[str, JsonValue]


def _default(obj: object) -> object:
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def loads(s: str) -> JsonValue:
    """Parse JSON string with floats as Decimal."""
    from json import loads as json_loads

    return cast(JsonValue, json_loads(s, parse_float=Decimal))


def load(f: IO[str]) -> JsonValue:
    """Load JSON with floats parsed as Decimal."""
    return loads(f.read())


def dumps(obj: JsonValue, *, indent: int | None = None) -> str:
    """Serialize to JSON string, Decimal as float."""
    from json import dumps as json_dumps

    return json_dumps(obj, indent=indent, default=_default)


def dump(obj: JsonValue, f: IO[str], *, indent: int | None = None) -> None:
    """Dump JSON, serializing Decimal as float."""
    _ = f.write(dumps(obj, indent=indent))
