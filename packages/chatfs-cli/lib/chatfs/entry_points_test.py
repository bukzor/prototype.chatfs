"""Every `main()` is a command, and every command is a `main()`.

A leaf's two spellings -- its module path and its `$PATH` name -- are one
string with different separators (`design.kb/040-design.kb/cli-command-shape.md`).
Nothing enforces that while you work: a new leaf with no `[project.scripts]`
line just never installs, and a renamed module leaves an entry pointing at
nothing until someone happens to run it. This is the enforcement.
"""

import ast
import tomllib
from collections.abc import Mapping
from typing import cast
from pathlib import Path

PACKAGE = Path(__file__).parents[2]


def command_for(module: str) -> str:
    """The `$PATH` name for a module path: segments joined by `-`, with `_`
    becoming `-` inside a segment.

    A bare-noun driver lives in its noun package's `__main__` and is named
    for the noun alone -- the absent verb reads as "all of them, in order".
    """
    parts = module.split(".")
    if parts[-1] == "__main__":
        parts = parts[:-1]
    return "-".join(part.replace("_", "-") for part in parts)


def declared_scripts() -> dict[str, str]:
    """`[project.scripts]`, narrowed step by step -- `tomllib` hands back
    `Any`, and a packaging check that silently accepts the wrong shape is
    worse than no check."""
    toml: dict[str, object] = tomllib.loads(
        (PACKAGE / "pyproject.toml").read_bytes().decode()
    )
    project = toml["project"]
    assert isinstance(project, Mapping), project
    scripts: object = project["scripts"]
    assert isinstance(scripts, Mapping), scripts
    # tomllib types every value `Any`, so the assertions above are the real
    # check; the cast only tells pyright what a console-script table is.
    return dict(cast(Mapping[str, str], scripts))


def modules_defining_main() -> dict[str, str]:
    """Command name -> `module:main`, for every non-test module that defines a
    module-level `main`. Parsed rather than imported: this must see a leaf
    whose dependencies are broken, and importing every module to find its
    entry points is how a packaging check becomes an integration test."""
    lib = PACKAGE / "lib"
    found: dict[str, str] = {}
    for py in sorted((lib / "chatfs").rglob("*.py")):
        if py.name.endswith("_test.py"):
            continue
        tree = ast.parse(py.read_bytes().decode())
        if not any(
            isinstance(node, ast.FunctionDef) and node.name == "main"
            for node in tree.body
        ):
            continue
        module = ".".join(py.relative_to(lib).with_suffix("").parts)
        found[command_for(module)] = f"{module}:main"
    return found


class DescribeCommandFor:
    def it_joins_module_segments_with_dashes(self):
        assert (
            command_for("chatfs.provider.claude.conversation.url_browse")
            == "chatfs-provider-claude-conversation-url-browse"
        )

    def it_names_a_bare_noun_driver_for_its_noun(self):
        assert (
            command_for("chatfs.provider.chatgpt.index.__main__")
            == "chatfs-provider-chatgpt-index"
        )


class DescribeEntryPoints:
    def it_declares_a_command_for_every_main(self):
        assert sorted(set(modules_defining_main()) - set(declared_scripts())) == []

    def it_declares_no_command_without_a_main(self):
        assert sorted(set(declared_scripts()) - set(modules_defining_main())) == []

    def it_points_each_command_at_the_module_its_name_spells(self):
        assert declared_scripts() == modules_defining_main()
