"""Which index item a url browse places (browse-incidental-capture.md)."""

from collections.abc import Mapping

import pytest
from typed_json import JsonObject

from chatfs.url_browse import choose_meta
from chatfs.user_error import UserError

Item = Mapping[str, str]

OLD: Item = {"id": "u", "title": "t", "update_time": "2025"}
NEW: Item = {"id": "u", "title": "t", "update_time": "2026"}
RENAMED: Item = {"id": "u", "title": "t2", "update_time": "2026"}


def identity(item: Item) -> JsonObject:
    return {"id": item["id"], "title": item["title"]}


def choose(on_disk: Item | None, in_sidebar: Item | None) -> Item:
    return choose_meta("u", on_disk, in_sidebar, identity, "chatgpt")


class DescribeChooseMeta:
    def it_keeps_what_is_on_disk_over_a_fresher_sidebar(self):
        assert choose(OLD, NEW) is OLD

    def it_keeps_what_is_on_disk_when_the_sidebar_lacks_the_chat(self):
        assert choose(OLD, None) is OLD

    def it_takes_the_sidebar_item_when_nothing_is_on_disk(self):
        assert choose(None, NEW) is NEW

    def it_refuses_a_sidebar_whose_identity_disagrees_with_disk(self):
        with pytest.raises(UserError, match="title: 't' != 't2'"):
            _ = choose(OLD, RENAMED)

    def it_refuses_when_neither_has_the_chat(self):
        with pytest.raises(UserError, match="chatfs-provider-chatgpt-index"):
            _ = choose(None, None)
