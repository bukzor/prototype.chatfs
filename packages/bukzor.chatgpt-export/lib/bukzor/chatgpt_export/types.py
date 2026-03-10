"""Shared type definitions for chatgpt_export."""

from collections.abc import Mapping

type JsonValue = None | bool | int | float | str | list[JsonValue] | JsonObj
type JsonObj = Mapping[str, JsonValue]
