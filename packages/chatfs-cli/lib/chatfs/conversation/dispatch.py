"""Pick a provider from the locator, then run that provider's own leaf.

Delegation is a subprocess (`python -m chatfs.provider.<p>.conversation.<leaf>`)
carrying the original argv untouched, the same way an orchestrator invokes a
stage. The dispatcher therefore parses only enough to name the provider --
`--cache` and every other argument stay the leaf's business, which is what
keeps this from becoming a second, drifting copy of each leaf's argv contract.
"""

from collections.abc import Sequence
from urllib.parse import urlparse

from chatfs.provider.registry import PROVIDERS, PROVIDER_BY_HOST
from chatfs.shell import sh as chatfs_sh
from chatfs.shell.place import resolve_chat_dir


def provider_for_url(url: str) -> str:
    """The provider serving `url`, by host.

    Host is the whole basis: it is what a link actually carries, and the
    three are disjoint by construction rather than by coincidence.
    """
    host = urlparse(url).netloc
    assert host in PROVIDER_BY_HOST, (host, sorted(PROVIDER_BY_HOST))
    return PROVIDER_BY_HOST[host]


def provider_for_path(arg: str) -> str:
    """The provider owning the chat dir `arg` points into, by cache segment.

    `resolve_chat_dir` yields `$cache/$provider/.chat/$UUID`, so the provider
    is a path segment -- read, not inferred. Deliberately not a `meta.json`
    shape sniff: two providers' index items differ only in which second
    timestamp field they carry, and one of those is an upstream payload we
    are required to store verbatim.
    """
    provider = resolve_chat_dir(arg).parent.parent.name
    assert provider in PROVIDERS, (provider, sorted(PROVIDERS))
    return provider


def run_leaf(provider: str, leaf: str, argv: Sequence[str]) -> None:
    import sys

    _ = chatfs_sh.run(
        [sys.executable, "-m", f"chatfs.provider.{provider}.conversation.{leaf}", *argv]
    )


def url_in(argv: Sequence[str]) -> str | None:
    """The first URL-shaped argument, or None if there is none.

    A scheme is the whole test: every other argument a url-addressed leaf
    accepts is a flag or a directory, neither of which carries one.
    """
    return next((arg for arg in argv if "://" in arg), None)
