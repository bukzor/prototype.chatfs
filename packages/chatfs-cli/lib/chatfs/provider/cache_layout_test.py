"""Where a provider's captures land, checked by running the real commands.

`index` and `refresh` are drivers: they parse `--cache`, append their
provider segment, and spawn child stages that parse `--cache` again. The
layout therefore lives *between* the commands -- a stage that hands its
own already-appended root to a child buries the whole cache one
directory deeper, and every stage's unit test still passes. So these run
the commands as processes, with argv and spawning intact, and look at
the tree that results.

The stub `har-browse` in `cache_layout_test/` is what makes that
affordable: it replays a canned CDP stream chosen by the test, so there
is no browser and no network. Every chat in those streams is dated years
back, which keeps `refresh` from wanting to capture a conversation --
what refresh is here to exercise is the index it spawns first.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

import pytest

from typed_json import JsonValue
from chatfs.cli import CACHE_ENV_VAR
from chatfs.provider.aistudio.index import browse as aistudio_browse
from chatfs.provider.chatgpt.index import browse as chatgpt_browse
from chatfs.provider.claude.index import browse as claude_browse
from chatfs.provider.registry import PROVIDERS

STUB_BIN = Path(__file__).with_suffix("")
"""Holds the `har-browse` the tests put first on PATH."""

STAMP = datetime(2020, 6, 15, 12, tzinfo=timezone.utc)
"""Every fixture chat's create/update time -- far enough back that no
plausible refresh window contains it, and mid-year mid-day so its local
year is 2020 under any offset."""

STAMP_ISO = STAMP.isoformat().replace("+00:00", "Z")
VIEW_YEAR = STAMP.astimezone().year
TITLE = "A chat from 2020"
REFRESH_DAYS = "7"


def cdp_response(url: str, body: JsonValue) -> str:
    """One CDP capture line, shaped the way chatfs.pluck.iter_responses
    reads it: the response body as an embedded JSON string."""
    event = {
        "method": "Network.responseReceived",
        "params": {"response": {"url": url, "body": json.dumps(body)}},
    }
    return json.dumps(event) + "\n"


def jspb(slots: dict[int, JsonValue]) -> list[JsonValue]:
    """A JSPB message: field numbers as list positions, unset slots null.

    AI Studio's wire format, and the only shape
    `chatfs.provider.aistudio.conversation.massage_json` can name.
    """
    return [slots.get(i) for i in range(max(slots) + 1)]


class Provider(NamedTuple):
    """One provider's index capture, reduced to a single chat.

    `browse_url` is the page its `index browse` asks for and the only
    one the stub will answer; `response_url` is the API response the
    provider's pluck selects out of the capture, which is a different
    URL entirely.
    """

    name: str
    browse_url: str
    response_url: str
    index_body: JsonValue
    chat_id: str
    view_label: str


CLAUDE = Provider(
    name="claude",
    browse_url=claude_browse.URL,
    response_url="https://claude.ai/api/organizations/org/chat_conversations_v2?limit=30",
    index_body={
        "data": [
            {
                "uuid": "11111111-1111-1111-1111-111111111111",
                "name": TITLE,
                "created_at": STAMP_ISO,
                "updated_at": STAMP_ISO,
            }
        ],
        "has_more": False,
    },
    chat_id="11111111-1111-1111-1111-111111111111",
    view_label="Created",
)

CHATGPT = Provider(
    name="chatgpt",
    browse_url=chatgpt_browse.URL,
    response_url="https://chatgpt.com/backend-api/conversations?offset=0&limit=28",
    index_body={
        "items": [
            {
                "id": "22222222-2222-2222-2222-222222222222",
                "title": TITLE,
                "create_time": STAMP_ISO,
                "update_time": STAMP_ISO,
            }
        ]
    },
    chat_id="22222222-2222-2222-2222-222222222222",
    view_label="Created",
)

AISTUDIO = Provider(
    name="aistudio",
    browse_url=aistudio_browse.URL,
    response_url=(
        "https://alkalimakersuite-pa.clients6.google.com/$rpc"
        "/google.internal.alkali.applications.makersuite.v1"
        ".MakerSuiteService/ListPrompts"
    ),
    # `[[entry, ...]]`, per pluck_index_pages. The entry's slots are
    # PROMPT's: name, metadata (displayName, lastModified.revisionTime),
    # and the empty chunkedPrompt an index entry always carries -- which
    # is why the view lands under `LastModified=`, there being no turn
    # content to read a creation time from.
    index_body=[
        [
            jspb(
                {
                    0: "prompts/3333cccc3333",
                    4: jspb(
                        {
                            0: TITLE,
                            4: jspb({0: [str(int(STAMP.timestamp())), 0]}),
                        }
                    ),
                    13: [],
                }
            )
        ]
    ],
    chat_id="3333cccc3333",
    view_label="LastModified",
)

ALL = (CLAUDE, CHATGPT, AISTUDIO)
IDS = [provider.name for provider in ALL]


def prepare(
    provider: Provider, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """Point the pipeline at an empty cache and the stub browser; return
    the cache root.

    Dropping $CHATFS_CACHE is load-bearing, not hygiene: a stage that
    never sees `--cache` falls back to it, which in a developer's shell
    is a real cache and a real browser window.
    """
    monkeypatch.delenv(CACHE_ENV_VAR, raising=False)
    monkeypatch.setenv("PATH", f"{STUB_BIN}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("CHATFS_STUB_URL", provider.browse_url)

    cdp = tmp_path / f"{provider.name}-index.cdp.jsonl"
    _ = cdp.write_text(cdp_response(provider.response_url, provider.index_body))
    monkeypatch.setenv("CHATFS_STUB_CDP", str(cdp))

    return tmp_path / "cache"


def run_command(module: str, *args: str) -> str:
    """Run one chatfs command to completion; return its stdout."""
    done = subprocess.run(
        [sys.executable, "-m", module, *args],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, (module, args, done.stdout, done.stderr)
    return done.stdout


def provider_dirs(cache: Path) -> list[str]:
    """Every real directory under `cache` named for a provider, as a
    path relative to `cache`.

    Symlinks are excluded: the view tree is symlinks all the way down,
    and one of them could legitimately be named after a provider (it is
    a chat's title).
    """
    found: list[str] = []
    for parent, dirnames, _ in os.walk(cache):
        for name in dirnames:
            path = Path(parent, name)
            if name in PROVIDERS and not path.is_symlink():
                found.append(str(path.relative_to(cache)))
    return sorted(found)


def assert_one_provider_dir(cache: Path, provider: Provider) -> None:
    """The whole bug class in one assertion: a provider's segment appears
    exactly once in the cache, at the top."""
    found = provider_dirs(cache)
    assert found == [provider.name], (
        f"the cache grew a provider directory below its root: {found} "
        f"-- a command appended its provider segment to a root that "
        f"already carried it, burying every capture one level deeper"
    )
    assert sorted(p.name for p in cache.iterdir()) == [provider.name], sorted(
        cache.iterdir()
    )


def assert_chat_placed(cache: Path, provider: Provider) -> None:
    """The indexed chat's two artifacts: its stored meta.json, and the
    one view symlink that leads a human to it."""
    root = cache / provider.name
    meta = root / ".data" / provider.chat_id / "meta.json"
    assert meta.is_file(), sorted(str(p) for p in root.rglob("*"))

    pattern = f"{provider.view_label}={VIEW_YEAR}/*/*/*/*"
    views = [p for p in root.glob(pattern) if p.is_symlink()]
    assert [p.name for p in views] == [TITLE], sorted(str(p) for p in root.rglob("*"))
    assert views[0].resolve() == root / ".chat" / provider.chat_id


class DescribeProviderCache:
    @pytest.mark.parametrize("provider", ALL, ids=IDS)
    def it_places_an_indexed_chat_under_one_provider_directory(
        self, provider: Provider, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        cache = prepare(provider, tmp_path, monkeypatch)

        stdout = run_command(
            f"chatfs.provider.{provider.name}.index", "--cache", str(cache)
        )

        assert [json.loads(line)["id"] for line in stdout.splitlines()] == [
            provider.chat_id
        ], stdout
        assert_one_provider_dir(cache, provider)
        assert_chat_placed(cache, provider)

    @pytest.mark.parametrize("provider", ALL, ids=IDS)
    def it_stays_flat_when_refresh_spawns_the_index(
        self, provider: Provider, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Refresh runs the index driver as a subprocess of its own --
        the same forwarding the drivers get wrong, one level further
        out."""
        cache = prepare(provider, tmp_path, monkeypatch)

        _ = run_command(
            f"chatfs.provider.{provider.name}.refresh",
            "--cache",
            str(cache),
            REFRESH_DAYS,
        )

        assert_one_provider_dir(cache, provider)
        assert_chat_placed(cache, provider)
