#!/usr/bin/env python3
"""Correlate a jspb (positional) body with its alt=json (named) twin → slot maps.

Step 3 of the reproducibility loop (see ../README.md). This is an *aid* for
authoring convert.py's SCHEMA, not an oracle: it proposes `slot -> field-name`
maps per message type by walking the named tree and the positional tree together.

Default (align) — assumes proto field-number ordering: alt=json emits fields in
ascending field number, so the matching jspb slots rise monotonically. We walk
each named field in order and claim the next type-compatible jspb slot.

    KNOWN LIMITATION — when a field is ABSENT in this instance, its slot is null
    and the monotonic claim skips ahead, so a later field can be mis-assigned to
    an earlier slot (e.g. with `isMe` absent, `photoUri` is claimed at slot 1,
    not its true slot 2). Cross-check every proposal against the bundle field
    numbers (../walk-graph.py) and the populated-slot tree (../body-shape.py)
    before trusting it. This is why SCHEMA is hand-curated. See
    ../discourse.kb/questions.kb/can-we-decode-deterministically.md.

--values (derive) — the other lens: for each named leaf value, list every jspb
index-path holding that value. Useful to locate a specific field by hand when
the ordering heuristic is ambiguous.

    ./correlate.py [JSPB ALT]            # slot maps (default)
    ./correlate.py --values [JSPB ALT]   # value -> jspb index-paths
"""

import sys
from collections.abc import Callable, Iterator

from convert import is_mapping, is_sequence, load_json
from verify import subject_of

FIXTURE_JSPB = "listprompts.jspb.json"
FIXTURE_ALT = "listprompts.alt-json.json"


def representative_resolvedrive(named: object, pos: object) -> tuple[object, object]:
    assert is_mapping(named), named
    assert is_sequence(pos), pos
    return named["prompt"], pos[0]


def representative_listprompts(named: object, pos: object) -> tuple[object, object]:
    assert is_mapping(named), named
    assert is_sequence(pos), pos
    named_prompts, pos_prompts = named["prompts"], pos[0]
    assert is_sequence(named_prompts), named_prompts
    assert is_sequence(pos_prompts), pos_prompts
    return named_prompts[0], pos_prompts[0]


# One representative-entry accessor per subject: align() wants a single
# named-dict/positional-list pair, not resolvedrive's singular prompt or
# listprompts' repeated page of them.
REPRESENTATIVE: dict[str, Callable[[object, object], tuple[object, object]]] = {
    "resolvedrive": representative_resolvedrive,
    "listprompts": representative_listprompts,
}


def kind(v: object) -> str:
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, (int, float)):
        return "num"
    if isinstance(v, str):
        return "str"
    if is_mapping(v):
        return "dict"
    if is_sequence(v):
        return "list"
    return "null"


def compatible(named: object, pos: object) -> bool:
    """Could this named value be encoded by this jspb slot value?"""
    if pos is None:
        return False
    nk, pk = kind(named), kind(pos)
    if nk == "bool":
        return pk == "num" and pos in (0, 1)
    if nk == "num":
        return pk == "num"
    if nk == "str":
        return pk in ("str", "num")  # enums encode as num
    if nk == "list":
        return pk == "list"
    if nk == "dict":
        return pk == "list"
    return True


def align(
    named: object, pos: object, path: str, schema: dict[str, dict[str, int]]
) -> None:
    """Record proposed slot maps into `schema`, keyed by message-type path."""
    if is_mapping(named) and is_sequence(pos):
        slots = schema.setdefault(path, {})
        cursor = 0
        for key, value in named.items():
            slot = next(
                (i for i in range(cursor, len(pos)) if compatible(value, pos[i])),
                None,
            )
            if slot is None:
                continue
            slots[key] = slot
            cursor = slot + 1
            align(value, pos[slot], f"{path}/{key}", schema)
    elif is_sequence(named) and is_sequence(pos):
        for elem_named, elem_pos in zip(named, pos):
            align(elem_named, elem_pos, f"{path}/[]", schema)
    # scalars: nothing to record


def leaves(
    node: object, path: tuple[object, ...] = ()
) -> Iterator[tuple[tuple[object, ...], object]]:
    if is_mapping(node):
        for k, v in node.items():
            yield from leaves(v, path + (k,))
    elif is_sequence(node):
        for i, v in enumerate(node):
            yield from leaves(v, path + (i,))
    else:
        yield path, node


def print_align(named: object, pos: object) -> None:
    schema: dict[str, dict[str, int]] = {}
    align(named, pos, "prompt", schema)
    for path in sorted(schema):
        print(path)
        for key, slot in sorted(schema[path].items(), key=lambda kv: kv[1]):
            print(f"    {slot:>3}  {key}")


def print_values(named: object, pos: object) -> None:
    """For each named leaf, show where its value occurs in the jspb array."""
    index: dict[object, list[str]] = {}
    for p, v in leaves(pos):
        if isinstance(v, (str, int, float)) and v != "":
            index.setdefault(v, []).append("/".join(map(str, p)))
    for p, v in leaves(named):
        if not isinstance(v, (str, int, float)) or v == "":
            continue
        hits = index.get(v, [])
        shown = " ; ".join(hits[:4]) + (" …" if len(hits) > 4 else "")
        print(f"{'/'.join(map(str, p))}\t=> {shown}")


def main() -> None:
    argv = sys.argv[1:]
    values = "--values" in argv
    argv = [a for a in argv if a != "--values"]
    jspb_path = argv[0] if argv else FIXTURE_JSPB
    alt_path = argv[1] if len(argv) > 1 else FIXTURE_ALT

    with open(jspb_path) as fp:
        pos = load_json(fp)
    with open(alt_path) as fp:
        named = load_json(fp)

    assert is_sequence(pos), pos
    assert is_mapping(named), named
    # Correlate on one representative entry — align() expects a single
    # named-dict/positional-list pair, not a repeated list of them.
    named_prompt, pos_prompt = REPRESENTATIVE[subject_of(jspb_path)](named, pos)

    if values:
        print_values(named_prompt, pos_prompt)
    else:
        print_align(named_prompt, pos_prompt)


if __name__ == "__main__":
    main()
