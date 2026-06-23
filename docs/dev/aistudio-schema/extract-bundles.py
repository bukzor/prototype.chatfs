#!/usr/bin/env python3
"""Extract the AI Studio boq-makersuite JS modules from a CDP capture into
`bundles/<module-id>.js` — one file per module, raw (minified) bytes.

Formatting is a separate concern: pipe these through prettier afterward
(`prettier --write bundles/*.js`) so the schema walk reads beautified source.
The walk tools (`walk-graph.py`, `grep-accessors.sh`) read per-module files.

Usage:
    ./extract-bundles.py [OUTDIR] < CAPTURE.jsonl   # OUTDIR default: bundles/

Module id: the `m=<id>` segment of the gstatic module URL (`_b`, `AgQvWc`, ...).
Bodies are deduped; a tag collision with differing content gets a `~N` suffix.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTDIR = os.path.join(HERE, "bundles")

MODULE_ID = re.compile(r"/m=([A-Za-z0-9_]+)")


def module_id(url):
    """The `m=<id>` module name from a gstatic boq URL, else 'unknown'."""
    m = MODULE_ID.search(url)
    return m.group(1) if m else "unknown"


def bundle_responses(events):
    """(module-id, body) for each boq-makersuite JS module response."""
    for event in events:
        if event.get("method") != "Network.responseReceived":
            continue
        response = event["params"]["response"]
        url = response.get("url", "")
        body = response.get("body")
        if "boq-makersuite" in url and "/js/" in url and isinstance(body, str):
            yield module_id(url), body


def collect(events):
    """{tag: body}, deduped by body; distinct bodies under one id get `~N`."""
    by_tag = {}
    bodies_seen = set()
    for tag, body in bundle_responses(events):
        if body in bodies_seen:
            continue
        bodies_seen.add(body)
        name, n = tag, 1
        while name in by_tag:
            name, n = f"{tag}~{n}", n + 1
        by_tag[name] = body
    return by_tag


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTDIR

    modules = collect(json.loads(line) for line in sys.stdin)
    os.makedirs(outdir, exist_ok=True)
    for tag, body in modules.items():
        with open(os.path.join(outdir, f"{tag}.js"), "w") as f:
            f.write(body)
    print(f"extracted {len(modules)} module(s) to {outdir}", file=sys.stderr)


if __name__ == "__main__":
    main()
