"""Tests for chatfs.layout's pure path vocabulary -- previously untested
(see .claude/todo.md's "Next" item), even though the Created=/LastModified=
label switch (2026-07-11) landed with none."""

import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from chatfs.layout import chat_dir_for, data_dir_for, data_dir_of, time_dir_for

# Epoch matches the AI Studio demo capture fixture used elsewhere in this
# incubator; under America/Chicago (CDT, UTC-5) it's 2026-06-20T12:42:40.
DEMO_EPOCH = 1781977360


def use_chicago_tz(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TZ", "America/Chicago")
    time.tzset()


class DescribeTimeDirFor:
    def it_labels_with_created_by_default(self, monkeypatch: pytest.MonkeyPatch):
        use_chicago_tz(monkeypatch)
        dt = datetime.fromtimestamp(DEMO_EPOCH, tz=timezone.utc)
        assert time_dir_for(dt) == Path("Created=2026/06/20/12:42:40-05:00")

    def it_labels_with_a_given_label(self, monkeypatch: pytest.MonkeyPatch):
        use_chicago_tz(monkeypatch)
        dt = datetime.fromtimestamp(DEMO_EPOCH, tz=timezone.utc)
        assert time_dir_for(dt, label="LastModified") == Path(
            "LastModified=2026/06/20/12:42:40-05:00"
        )


class DescribeDataDirOf:
    def it_derives_the_data_dir_from_a_chat_dir(self, tmp_path: Path):
        chat_dir = chat_dir_for("abc123", tmp_path)
        assert data_dir_of(chat_dir) == data_dir_for("abc123", tmp_path)
