"""Shared argv parsing for the --cache-taking leaf commands.

Kept pure per chatfs/__init__.py's convention -- takes argv and environ
explicitly rather than reading sys.argv/os.environ itself -- so every
leaf's main() stays the only place that touches process globals.
"""

from collections.abc import Mapping, Sequence
from pathlib import Path

CACHE_ENV_VAR = "CHATFS_CACHE"


def extract_cache(
    argv: Sequence[str], environ: Mapping[str, str], provider: str
) -> tuple[Path | None, list[str]]:
    """Pull `--cache <dir>` out of argv at any position, falling back to
    $CHATFS_CACHE when the flag is absent. Returns the resolved absolute
    provider root -- `$cache/$provider/` -- or None when neither source
    supplies a cache, plus the remaining args with `--cache` and its
    value removed.

    Appending `provider` here rather than in each leaf is what lets one
    `--cache`/$CHATFS_CACHE value serve every provider: a leaf that
    forgot the append would spill its capture into the cache root
    itself, where it is indistinguishable from another provider's.

    A dangling `--cache` with no following value is dropped rather than
    raising -- it's a routine typo, not a bug; the caller's own usage
    check (root is None) reports it the same way as no --cache at all.

    Resolving to an absolute path here, once, is what makes every
    downstream chat_dir/data_dir absolute -- both the chat.md path a
    leaf command prints and the `.data` inspection symlink depend on it.
    """
    rest = list(argv)
    cache: str | None = None
    if "--cache" in rest:
        i = rest.index("--cache")
        if i + 1 < len(rest):
            cache = rest[i + 1]
            del rest[i : i + 2]
        else:
            del rest[i:]
    if cache is None:
        cache = environ.get(CACHE_ENV_VAR)
    if not cache:
        return None, rest
    return Path(cache).resolve() / provider, rest
