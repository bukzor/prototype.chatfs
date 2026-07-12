#!/usr/bin/env python3
"""Assert the converter's output is "similar enough" to AI Studio's real alt=json.

Step 5 of the reproducibility loop (see ../README.md). Convert a positional JSPB
body with convert.py, then compare it against the named alt=json the server
returned for the *same* prompt — by FIELD NAME and STRUCTURE only.

Leaf values legitimately differ between the two encodings and are NOT compared:
    bools       jspb 0 / 1              vs  alt-json false / true
    enums       jspb ints              vs  alt-json names ("OFF", "HARM_CATEGORY_…")
    timestamps  jspb [seconds, nanos]  vs  alt-json RFC3339 string

The timestamp case differs in SHAPE (list vs scalar), so the structural diff
treats a short all-numeric list as scalar-equivalent — the one tolerated shape
gap. Every other shape or name mismatch is a real divergence.

    ./verify.py                    # every endpoint/*/ with a golden pair (default)
    ./verify.py endpoint/listprompts endpoint/resolvedrive   # specific endpoints

No-arg mode discovers endpoints by directory: every `endpoint/*/` holding a
`jspb.json` + `alt-json.json` pair. Each is checked independently — one
endpoint's divergence doesn't hide another's, and doesn't block reporting on
the rest.

Exit 0 when ALL endpoints' names + shape match; 1 (with a divergence report on
stderr per failing endpoint) otherwise.
"""

import sys
from pathlib import Path

from convert import from_jspb, is_mapping, is_sequence, load_json, load_meta

JSPB_NAME = "jspb.json"
ALT_NAME = "alt-json.json"


def discover_endpoints() -> list[Path]:
    """Every `endpoint/*/` directory holding a jspb.json + alt-json.json pair."""
    dirs: list[Path] = []
    for jspb_path in sorted(Path("endpoint").glob(f"*/{JSPB_NAME}")):
        endpoint_dir = jspb_path.parent
        assert (endpoint_dir / ALT_NAME).exists(), f"{endpoint_dir} has no {ALT_NAME}"
        dirs.append(endpoint_dir)
    assert dirs, (
        "no endpoint/*/jspb.json found — run from rosetta/, or pass ENDPOINT_DIR"
    )
    return dirs


def is_number(v: object) -> bool:
    """A jspb numeric scalar — int/float, or the digit-string jspb uses for int64."""
    if isinstance(v, bool):
        return False
    if isinstance(v, (int, float)):
        return True
    return isinstance(v, str) and v.lstrip("-").isdigit()


def is_timestamp(v: object) -> bool:
    """A jspb timestamp slot: a 1- or 2-element numeric list, [seconds[, nanos]].

    jspb encodes the int64 seconds as a *string* (JS precision), so element
    types are mixed — a digit-string and an int.
    """
    return is_sequence(v) and 1 <= len(v) <= 2 and all(is_number(e) for e in v)


def is_scalar(v: object) -> bool:
    return not is_mapping(v) and not is_sequence(v)


def timestamp_match(a: object, b: object) -> bool:
    """One side a jspb [s, ns] pair, the other an RFC3339 scalar — tolerated."""
    return (is_timestamp(a) and is_scalar(b)) or (is_scalar(a) and is_timestamp(b))


def kind(v: object) -> str:
    if is_mapping(v):
        return "dict"
    if is_sequence(v):
        return "list"
    return "scalar"


def diff(ours: object, real: object, path: str, out: list[str]) -> None:
    """Append a divergence line for every name/shape mismatch between the trees."""
    if is_mapping(ours) and is_mapping(real):
        for k in ours.keys() - real.keys():
            out.append(f"only in OURS: {path}/{k}")
        for k in real.keys() - ours.keys():
            out.append(f"only in REAL: {path}/{k}")
        for k in ours.keys() & real.keys():
            diff(ours[k], real[k], f"{path}/{k}", out)
    elif is_sequence(ours) and is_sequence(real):
        if len(ours) != len(real):
            out.append(f"len {len(ours)} != {len(real)} at {path}")
        for i, (x, y) in enumerate(zip(ours, real)):
            diff(x, y, f"{path}/{i}", out)
    elif timestamp_match(ours, real):
        pass  # jspb [s, ns] vs alt-json RFC3339 string — the one tolerated gap
    elif kind(ours) != kind(real):
        out.append(f"shape {kind(ours)} vs {kind(real)} at {path}")
    # both scalar leaves: values may differ (bool/enum/etc.) — not compared


def check_endpoint(endpoint_dir: Path) -> bool:
    """Convert + diff one endpoint's pair; print its OK/DIVERGENT report.

    Returns True if OK.
    """
    meta = load_meta(endpoint_dir)
    with open(endpoint_dir / JSPB_NAME) as fp:
        ours = from_jspb(load_json(fp), meta)
    with open(endpoint_dir / ALT_NAME) as fp:
        real = load_json(fp)

    out: list[str] = []
    diff(ours, real, "", out)

    if out:
        print(
            f"DIVERGENT: {endpoint_dir}/{JSPB_NAME} -> json  vs  {ALT_NAME}",
            file=sys.stderr,
        )
        for line in out:
            print(f"  {line}", file=sys.stderr)
        return False
    print(
        f"OK: {endpoint_dir}/{JSPB_NAME} converts similar-enough to {ALT_NAME}",
        file=sys.stderr,
    )
    return True


def main() -> int:
    if len(sys.argv) > 1:
        endpoints = [Path(a) for a in sys.argv[1:]]
    else:
        endpoints = discover_endpoints()

    results = [check_endpoint(d) for d in endpoints]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
