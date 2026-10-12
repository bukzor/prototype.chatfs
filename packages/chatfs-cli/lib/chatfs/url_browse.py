"""Shared helpers for `conversation url browse` orchestrators.

A url-browse orchestrator for a provider with two endpoints (an index
page incidentally captured alongside the conversation document — see
design.kb/040-design.kb/browse-incidental-capture.md) cross-checks the
two, null-tolerant, to catch schema drift between them. Only claude and
chatgpt have two endpoints today; AI Studio's single
`ResolveDriveResource` body carries both identity and turn content, so
it has nothing to cross-check.
"""
from collections.abc import Callable, Mapping

from typed_json import JsonObject, JsonValue

from chatfs.user_error import UserError


def choose_meta[Item](
    uuid: str,
    on_disk: Item | None,
    in_sidebar: Item | None,
    identity: Callable[[Item], JsonObject],
    provider: str,
) -> Item:
    """The index item a url browse places: what's on disk, else what the
    sidebar captured (browse-incidental-capture.md, "Which meta.json wins").

    Raises UserError when neither has the chat, or when both do and their
    `identity` projections disagree.
    """
    recovery = (
        f"Run chatfs-provider-{provider}-index with the sidebar scrolled back "
        + "past this chat, then rerun this command."
    )
    if on_disk is not None:
        if in_sidebar is not None:
            mismatches = null_tolerant_mismatches(
                identity(on_disk), identity(in_sidebar)
            )
            if mismatches:
                raise UserError(
                    f"meta.json for {uuid} disagrees with the sidebar: "
                    + f"{'; '.join(mismatches)}. "
                    + recovery
                )
        return on_disk
    elif in_sidebar is not None:
        return in_sidebar
    else:
        raise UserError(
            f"no captured sidebar page included {uuid}, and no earlier index "
            + "placed its meta.json. "
            + recovery
        )


def null_tolerant_mismatches(
    a: Mapping[str, JsonValue], b: Mapping[str, JsonValue], prefix: str = ""
) -> list[str]:
    """Recursive key comparison; missing or None on either side is ok.

    Recurses into nested mappings so that one side carrying extra
    None-valued keys (common when one endpoint returns a superset
    schema with unset fields) does not register as a mismatch.
    """
    out: list[str] = []
    for k in set(a) | set(b):
        va, vb = a.get(k), b.get(k)
        if va is None or vb is None:
            continue
        path = f"{prefix}{k}"
        if isinstance(va, Mapping) and isinstance(vb, Mapping):
            out.extend(null_tolerant_mismatches(va, vb, prefix=f"{path}."))
            continue
        if va != vb:
            out.append(f"{path}: {va!r} != {vb!r}")
    return out
