"""Path conventions shared across providers.

`INCUBATOR_ROOT` is this file's own location, not `__file__` counted
from whichever leaf module needs it -- robust regardless of how deeply
nested a caller sits in `provider/<name>/...`, and computed once
instead of duplicated per file. Every provider anchors its demo tree at
`INCUBATOR_ROOT / "chatfs.demo" / <provider>`; `demo_root` names that
convention so call sites read as intent, not path arithmetic.
"""

from pathlib import Path

INCUBATOR_ROOT = Path(__file__).parent.parent


def demo_root(provider: str) -> Path:
    return INCUBATOR_ROOT / "chatfs.demo" / provider
