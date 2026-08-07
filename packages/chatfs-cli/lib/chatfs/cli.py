"""chatfs top-level CLI entry point."""

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="chatfs",
        description="Lazy filesystem for chat conversations (claude.ai, ChatGPT).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="chatfs 0.1.0 (pre-alpha)",
    )
    parser.parse_args(argv)
    print(
        "chatfs: pre-alpha. No subcommands wired yet. See docs/dev/design.kb/.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
