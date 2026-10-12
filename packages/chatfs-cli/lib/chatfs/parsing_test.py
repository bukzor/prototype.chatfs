"""A JSON error raised while reading a file names the file."""

import json
from pathlib import Path

import pytest
import typed_json

from chatfs.parsing import parsing


class DescribeParsing:
    def it_notes_the_absolute_path_on_a_decode_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.chdir(tmp_path)
        _ = (tmp_path / "empty.json").write_text("")

        with pytest.raises(json.JSONDecodeError) as excinfo:
            with parsing(Path("empty.json")):
                _ = typed_json.loads(Path("empty.json").read_text())

        assert excinfo.value.__notes__ == [f"while parsing {tmp_path}/empty.json"]

    def it_leaves_other_errors_alone(self, tmp_path: Path):
        with pytest.raises(KeyError) as excinfo:
            with parsing(tmp_path / "x.json"):
                raise KeyError("k")

        assert not hasattr(excinfo.value, "__notes__")
