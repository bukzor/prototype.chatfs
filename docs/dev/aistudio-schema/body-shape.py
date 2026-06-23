#!/usr/bin/env python3
"""Print the populated-index tree of a JSPB array.

Input (stdin): one JSPB value (JSON array) per line — e.g. the prompt body
from chatfs_aistudio_conversation_pluck.jq.
Args: optional MAXDEPTH (default 4).
Output (stdout): each non-null array slot as `idx` → descriptor, indented by
depth. JSPB array index = proto field number - 1, so this is the observed
counterpart to walk-graph.py's schema field numbers.
"""
import json
import sys


def descriptor(value):
    """Short one-line type/size hint for a JSPB slot value."""
    if isinstance(value, list):
        filled = sum(1 for v in value if v is not None)
        return f"list({len(value)}, {filled} set)"
    elif isinstance(value, str):
        return json.dumps(value[:48])
    else:
        return repr(value)


def show(value, depth, maxdepth, out):
    """Append `(indent, idx, descriptor)` rows for each non-null slot, recursing into lists."""
    if not isinstance(value, list) or depth > maxdepth:
        return
    for idx, slot in enumerate(value):
        if slot is None:
            continue
        out.append((depth, idx, descriptor(slot)))
        show(slot, depth + 1, maxdepth, out)


def main():
    maxdepth = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        out = []
        show(json.loads(line), 0, maxdepth, out)
        for depth, idx, desc in out:
            print(f"{'  ' * depth}[{idx}] {desc}")
        print()


if __name__ == "__main__":
    main()
