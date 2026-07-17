"""Crash-matrix and lifecycle tests for chatfs_atomic's stage-and-promote
kernel: recovery at each interruption point, file<->directory type changes,
.fail latest-wins/cleared-on-success, and the _exchange fallback path when
RENAME_EXCHANGE is unsupported."""

import fcntl
import os
from pathlib import Path

import pytest

import chatfs_atomic
from chatfs_atomic import read_locked, recover, staged, write_locked


def sibling(dst: Path, kind: str) -> Path:
    """The documented in-flight sibling path for `dst`: `.{name}.{kind}`."""
    return dst.parent / f".{dst.name}.{kind}"


def _unsupported_exchange(_a: Path, _b: Path) -> bool:
    return False


class DescribeStaged:
    def it_promotes_a_new_file(self, tmp_path: Path):
        dst = tmp_path / "thing"
        with staged(dst) as scratch:
            _ = scratch.write_text("v1")
        assert dst.read_text() == "v1"
        assert not sibling(dst, "tmp").exists()

    def it_promotes_a_new_directory(self, tmp_path: Path):
        dst = tmp_path / "thing"
        with staged(dst) as scratch:
            scratch.mkdir()
            _ = (scratch / "file").write_text("v1")
        assert (dst / "file").read_text() == "v1"

    def it_replaces_an_existing_file(self, tmp_path: Path):
        dst = tmp_path / "thing"
        _ = dst.write_text("old")
        with staged(dst) as scratch:
            _ = scratch.write_text("new")
        assert dst.read_text() == "new"

    def it_replaces_an_existing_directory(self, tmp_path: Path):
        dst = tmp_path / "thing"
        dst.mkdir()
        _ = (dst / "old_file").write_text("old")
        with staged(dst) as scratch:
            scratch.mkdir()
            _ = (scratch / "new_file").write_text("new")
        assert (dst / "new_file").read_text() == "new"
        assert not (dst / "old_file").exists()

    def it_replaces_a_file_destination_with_a_directory(self, tmp_path: Path):
        dst = tmp_path / "thing"
        _ = dst.write_text("old")
        with staged(dst) as scratch:
            scratch.mkdir()
            _ = (scratch / "file").write_text("new")
        assert dst.is_dir()
        assert (dst / "file").read_text() == "new"

    def it_replaces_a_directory_destination_with_a_file(self, tmp_path: Path):
        dst = tmp_path / "thing"
        dst.mkdir()
        _ = (dst / "old_file").write_text("old")
        with staged(dst) as scratch:
            _ = scratch.write_text("new")
        assert dst.is_file()
        assert dst.read_text() == "new"


class DescribeCrashRecovery:
    def it_preserves_a_crashed_populate_as_fail(self, tmp_path: Path):
        dst = tmp_path / "thing"
        with pytest.raises(RuntimeError), staged(dst) as scratch:
            _ = scratch.write_text("half-written")
            raise RuntimeError("boom")

        assert not dst.exists()
        assert sibling(dst, "fail").read_text() == "half-written"
        assert not sibling(dst, "tmp").exists()

        # a killed attempt doesn't block the next one
        with staged(dst) as scratch:
            _ = scratch.write_text("v1")
        assert dst.read_text() == "v1"

    def it_rotates_a_stale_tmp_to_fail_on_entry(self, tmp_path: Path):
        dst = tmp_path / "thing"
        _ = dst.write_text("v1")
        # simulates a process killed outright (no exception ever ran)
        _ = sibling(dst, "tmp").write_text("orphaned")

        with staged(dst) as scratch:
            # recover() already relabeled the orphan by the time we're yielded
            assert sibling(dst, "fail").read_text() == "orphaned"
            _ = scratch.write_text("v2")

        assert dst.read_text() == "v2"
        assert not sibling(dst, "fail").exists()  # this run succeeded


class DescribeRecover:
    def it_is_a_noop_when_nothing_is_stale(self, tmp_path: Path):
        dst = tmp_path / "thing"
        _ = dst.write_text("v1")
        recover(dst)
        assert dst.read_text() == "v1"

    def it_restores_the_old_version_when_killed_between_the_two_renames(
        self, tmp_path: Path
    ):
        dst = tmp_path / "thing"
        # rename 1 (dst -> .old) ran, rename 2 (.tmp -> dst) never did
        _ = sibling(dst, "old").write_text("old-version")
        _ = sibling(dst, "tmp").write_text("interrupted-candidate")

        recover(dst)

        assert dst.read_text() == "old-version"
        assert not sibling(dst, "old").exists()
        assert not sibling(dst, "tmp").exists()
        assert sibling(dst, "fail").read_text() == "interrupted-candidate"

    def it_discards_a_superseded_old_version_when_killed_before_cleanup(
        self, tmp_path: Path
    ):
        dst = tmp_path / "thing"
        # both renames ran; only the final .old cleanup was skipped
        _ = dst.write_text("new-version")
        _ = sibling(dst, "old").write_text("superseded-old")

        recover(dst)

        assert dst.read_text() == "new-version"
        assert not sibling(dst, "old").exists()
        assert not sibling(dst, "fail").exists()


class DescribeFailLifecycle:
    def it_keeps_only_the_latest_failure(self, tmp_path: Path):
        # directory-shaped: a plain-file fail would silently clobber via
        # rename(2)'s own semantics, masking a missing explicit removal
        dst = tmp_path / "thing"
        for content in ("first-failure", "second-failure"):
            with pytest.raises(RuntimeError), staged(dst) as scratch:
                scratch.mkdir()
                _ = (scratch / "content").write_text(content)
                raise RuntimeError("boom")

        assert (sibling(dst, "fail") / "content").read_text() == "second-failure"

    def it_clears_a_stale_fail_on_success(self, tmp_path: Path):
        dst = tmp_path / "thing"
        with pytest.raises(RuntimeError), staged(dst) as scratch:
            _ = scratch.write_text("failure")
            raise RuntimeError("boom")
        assert sibling(dst, "fail").exists()

        with staged(dst) as scratch:
            _ = scratch.write_text("success")

        assert dst.read_text() == "success"
        assert not sibling(dst, "fail").exists()


class DescribeExchangeFallback:
    def it_falls_back_to_swap_via_old_when_exchange_is_unsupported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setattr(chatfs_atomic, "_exchange", _unsupported_exchange)
        dst = tmp_path / "thing"
        dst.mkdir()
        _ = (dst / "old_file").write_text("old")

        with staged(dst) as scratch:
            scratch.mkdir()
            _ = (scratch / "new_file").write_text("new")

        assert (dst / "new_file").read_text() == "new"
        assert not (dst / "old_file").exists()
        assert not sibling(dst, "old").exists()

    def it_raises_on_an_unexpected_errno_instead_of_treating_it_as_unsupported(
        self, tmp_path: Path
    ):
        missing_a = tmp_path / "missing-a"
        missing_b = tmp_path / "missing-b"
        with pytest.raises(OSError):
            _ = chatfs_atomic._exchange(  # pyright: ignore[reportPrivateUsage]
                missing_a, missing_b
            )


class DescribeLocking:
    def it_takes_an_exclusive_lock_that_blocks_even_a_second_reader(
        self, tmp_path: Path
    ):
        # LOCK_SH (not LOCK_EX) as the probe: a second LOCK_EX attempt would
        # conflict with either lock type and couldn't tell them apart.
        with write_locked(tmp_path):
            fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
            try:
                with pytest.raises(BlockingIOError):
                    fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
            finally:
                os.close(fd)

    def it_allows_a_second_reader_under_a_shared_lock(self, tmp_path: Path):
        with read_locked(tmp_path):
            fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
            try:
                fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    def it_releases_the_lock_on_exit(self, tmp_path: Path):
        with write_locked(tmp_path):
            pass
        fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
