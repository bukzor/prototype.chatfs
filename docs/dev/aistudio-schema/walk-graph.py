#!/usr/bin/env python3
"""Walk an immutable-JS-proto message graph from a starting constructor.

Sources: one or more bundle files as args, else the bundle JS on stdin.
  ./walk-graph.py i9a bundles/*.js            # walk a ctor across all bundles
  ./walk-graph.py i9a < bundles/_b.js         # single bundle on stdin
  ./walk-graph.py --rpc ResolveDriveResource bundles/*.js   # walk by RPC method
Options: --rpc METHOD resolves the method's *response* ctor as the start;
  --depth N caps BFS depth (default 4).

A message's class body may live in a different bundle than its parent's, so
pass ALL bundles (`bundles/*.js`) — feeding a single bundle silently truncates
the graph at module boundaries (fields whose ctor is defined elsewhere read as
`<not a local class def>`).

Output: each reachable message and its fields, indented by depth:
  Prompt _.Qw:
    #1   idx0  _.l   Name
    #5   idx4  _.X   Metadata -> _.Mo
Field numbers come from the accessor's integer arg; `idx` is the JSPB array
index (number - 1). Message-typed fields (a ctor arg) are followed BFS. A `?`
after a primitive marks one not in LEGEND — recovered in number+name but not
yet typed (see README primitive legend).
"""
import re
import sys

# Whitespace-tolerant: the bundle ships beautified (newlines + indentation)
# in some modules and minified in others.
ACCESSOR = re.compile(
    r"get([A-Z][A-Za-z0-9]*)\(\)\s*\{\s*return\s+(_\.[A-Za-z0-9]+)\(this,([^)]*)\)"
)
CTOR = re.compile(r"_\.[A-Za-z0-9]+|[A-Za-z0-9$]+")

# Known accessor primitives (README legend). Anything outside this set is
# flagged in output so partial-typing coverage is visible during a walk.
LEGEND = {"_.l", "_.Mj", "_.X", "_.xi"}


def rpc_response_ctor(src, method):
    """The response ctor of MakerSuiteService/<method>, or None.

    Stub shape (prettified): the method path string is followed by the request
    ctor then the response ctor:
        "/…/MakerSuiteService/ResolveDriveResource",
        _.h9a,   # request
        i9a,     # response
    """
    m = re.search(
        r"MakerSuiteService/" + re.escape(method) + r'"\s*,\s*([\w$.]+)\s*,\s*([\w$.]+)',
        src,
    )
    return m.group(2) if m else None


def class_body(src, ctor):
    """The full `{…}` of `ctor=class extends …`, brace-matched, or None if absent.

    Brace-counting (quote-aware) rather than a `}};` scan: accessor bodies that
    return object literals end in `}}` and would stop a naive scan mid-class.
    """
    m = re.search(re.escape(ctor) + r"\s*=\s*class\s+extends", src)
    if m is None:
        return None
    open_brace = src.find("{", m.start())
    depth = 0
    quote = None
    i = open_brace
    while i < len(src):
        c = src[i]
        if quote is not None:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "\"'`":
            quote = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return src[open_brace : i + 1]
        i += 1
    return src[open_brace:]


def fields(body):
    """(number, prim, name, submsg-ctor|None) per accessor, in declaration order."""
    rows = []
    for name, prim, args in ACCESSOR.findall(body):
        toks = [t.strip() for t in args.split(",")]
        number = next(t for t in toks if t.isdigit())
        ctor = next((t for t in toks if t and not t.isdigit()), None)
        rows.append((int(number), prim, name, ctor))
    return rows


def walk(src, start, maxdepth):
    """BFS the message graph from `start`, yielding (depth, label, ctor, rows|None)."""
    seen = set()
    frontier = [(0, start, start)]
    while frontier:
        depth, label, ctor = frontier.pop(0)
        if ctor in seen or depth > maxdepth:
            continue
        seen.add(ctor)
        body = class_body(src, ctor)
        rows = fields(body) if body is not None else None
        yield depth, label, ctor, rows
        for *_, name, sub in rows or []:
            if sub and CTOR.fullmatch(sub):
                frontier.append((depth + 1, f"{label}.{name}", sub))


def main():
    args = sys.argv[1:]
    maxdepth = 4
    if "--depth" in args:
        i = args.index("--depth")
        maxdepth = int(args[i + 1])
        del args[i : i + 2]

    method = None
    if "--rpc" in args:
        i = args.index("--rpc")
        method = args[i + 1]
        del args[i : i + 2]

    start = None
    if not method:
        start, *args = args  # first positional is the start ctor

    files = args  # any remaining positionals are bundle files
    src = "".join(open(f).read() for f in files) if files else sys.stdin.read()

    if method:
        start = rpc_response_ctor(src, method)
        if start is None:
            sys.exit(f"no stub for MakerSuiteService/{method} in the given bundles")
        print(f"# {method} response -> {start}")

    for depth, label, ctor, rows in walk(src, start, maxdepth):
        pad = "  " * depth
        print(f"{pad}{label} {ctor}:")
        if rows is None:
            print(f"{pad}  <not a local class def>")
            continue
        for number, prim, name, sub in rows:
            edge = f" -> {sub}" if sub else ""
            flag = "" if prim in LEGEND else "?"
            print(f"{pad}  #{number:<3} idx{number - 1:<3} {prim + flag:6} {name}{edge}")


if __name__ == "__main__":
    main()
