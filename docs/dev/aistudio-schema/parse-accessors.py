#!/usr/bin/env python3
"""Parse immutable-JS-proto accessors into schema rows.

Input (stdin): one accessor per line, e.g. `getPrompt(){return _.X(this,_.Qw,1)}`.
Output (stdout): one JSON object per line:
  {"name": "Prompt", "number": 1, "prim": "_.X", "submsg": "_.Qw"}

`number` is the proto field number; `prim` is the accessor primitive (see
README legend); `submsg` is the constructor argument when present (the edge
to the next message), else null. Duplicate (name, number, prim, submsg) rows
collapse — the same field is read from many call sites.
"""
import json
import re
import sys

# Whitespace-agnostic: the accessor may arrive minified or prettified
# (the grep stage folds newlines to spaces but leaves prettier's spacing).
ACCESSOR = re.compile(r"^get([A-Za-z0-9]+)\(\)\s*\{\s*return\s+(_\.[A-Za-z0-9]+)\(this,(.*)\)$")


def parse_accessor(line):
    """Schema row for one accessor line; the lone integer arg is the field number."""
    match = ACCESSOR.match(line)
    assert match, line
    name, prim, argstr = match.groups()
    args = [a.strip() for a in argstr.split(",")]
    numbers = [a for a in args if a.isdigit()]
    assert numbers, line
    submsgs = [a for a in args if not a.isdigit()]
    return {
        "name": name,
        "number": int(numbers[0]),
        "prim": prim,
        "submsg": submsgs[0] if submsgs else None,
    }


def main():
    seen = set()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        row = parse_accessor(line)
        key = (row["name"], row["number"], row["prim"], row["submsg"])
        if key not in seen:
            seen.add(key)
            print(json.dumps(row))


if __name__ == "__main__":
    main()
