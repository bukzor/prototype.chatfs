"""Crash-matrix and lifecycle tests for chatfs.shell.atomic's stage-and-promote
kernel: recovery at each interruption point, file<->directory type changes,
.fail latest-wins/cleared-on-success, and the _exchange fallback path when
RENAME_EXCHANGE is unsupported."""

import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from chatfs.shell import atomic as chatfs_atomic
from chatfs.shell.atomic import recover, staged

INCUBATOR_ROOT = Path(__file__).parent.parent.parent


def sibling(dst: Path, kind: str) -> Path:
    """The documented in-flight sibling path for `dst`: `.{name}.{kind}`."""
    return dst.parent / f".{dst.name}.{kind}"


def _unsupported_exchange(_a: Path, _b: Path) -> bool:
    return False


class DescribeStaged:
    def it_promotes_a_new_file(self, tmp_path: Path):
        dst = tmp_path / "thing"
        with staged(dst, anchor=tmp_path) as scratch:
            _ = scratch.write_text("v1")
        assert dst.read_text() == "v1"
        assert not sibling(dst, "tmp").exists()

    def it_promotes_a_new_directory(self, tmp_path: Path):
        dst = tmp_path / "thing"
        with staged(dst, anchor=tmp_path) as scratch:
            scratch.mkdir()
            _ = (scratch / "file").write_text("v1")
        assert (dst / "file").read_text() == "v1"

    def it_replaces_an_existing_file(self, tmp_path: Path):
        dst = tmp_path / "thing"
        _ = dst.write_text("old")
        with staged(dst, anchor=tmp_path) as scratch:
            _ = scratch.write_text("new")
        assert dst.read_text() == "new"

    def it_replaces_an_existing_directory(self, tmp_path: Path):
        dst = tmp_path / "thing"
        dst.mkdir()
        _ = (dst / "old_file").write_text("old")
        with staged(dst, anchor=tmp_path) as scratch:
            scratch.mkdir()
            _ = (scratch / "new_file").write_text("new")
        assert (dst / "new_file").read_text() == "new"
        assert not (dst / "old_file").exists()

    def it_replaces_a_file_destination_with_a_directory(self, tmp_path: Path):
        dst = tmp_path / "thing"
        _ = dst.write_text("old")
        with staged(dst, anchor=tmp_path) as scratch:
            scratch.mkdir()
            _ = (scratch / "file").write_text("new")
        assert dst.is_dir()
        assert (dst / "file").read_text() == "new"

    def it_replaces_a_directory_destination_with_a_file(self, tmp_path: Path):
        dst = tmp_path / "thing"
        dst.mkdir()
        _ = (dst / "old_file").write_text("old")
        with staged(dst, anchor=tmp_path) as scratch:
            _ = scratch.write_text("new")
        assert dst.is_file()
        assert dst.read_text() == "new"


class DescribeCrashRecovery:
    def it_preserves_a_crashed_populate_as_fail(self, tmp_path: Path):
        dst = tmp_path / "thing"
        with pytest.raises(RuntimeError), staged(dst, anchor=tmp_path) as scratch:
            _ = scratch.write_text("half-written")
            raise RuntimeError("boom")

        assert not dst.exists()
        assert sibling(dst, "fail").read_text() == "half-written"
        assert not sibling(dst, "tmp").exists()

        # a killed attempt doesn't block the next one
        with staged(dst, anchor=tmp_path) as scratch:
            _ = scratch.write_text("v1")
        assert dst.read_text() == "v1"

    def it_rotates_a_stale_tmp_to_fail_on_entry(self, tmp_path: Path):
        dst = tmp_path / "thing"
        _ = dst.write_text("v1")
        # simulates a process killed outright (no exception ever ran)
        _ = sibling(dst, "tmp").write_text("orphaned")

        with staged(dst, anchor=tmp_path) as scratch:
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
            with pytest.raises(RuntimeError), staged(dst, anchor=tmp_path) as scratch:
                scratch.mkdir()
                _ = (scratch / "content").write_text(content)
                raise RuntimeError("boom")

        assert (sibling(dst, "fail") / "content").read_text() == "second-failure"

    def it_clears_a_stale_fail_on_success(self, tmp_path: Path):
        dst = tmp_path / "thing"
        with pytest.raises(RuntimeError), staged(dst, anchor=tmp_path) as scratch:
            _ = scratch.write_text("failure")
            raise RuntimeError("boom")
        assert sibling(dst, "fail").exists()

        with staged(dst, anchor=tmp_path) as scratch:
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

        with staged(dst, anchor=tmp_path) as scratch:
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


CHILDREN = Path(__file__).parent / "atomic_test"
CHILD_KILL_DURING_POPULATE = CHILDREN / "child_kill_during_populate.py"
CHILD_KILL_BETWEEN_RENAMES = CHILDREN / "child_kill_between_renames.py"
CHILD_KILL_BEFORE_OLD_CLEANUP = CHILDREN / "child_kill_before_old_cleanup.py"
CHILD_KILL_DURING_EXCHANGE_CLEANUP = CHILDREN / "child_kill_during_exchange_cleanup.py"


def kill_at_ready(script: Path, dst: Path, anchor: Path) -> None:
    """Run `script` (one of the CHILD_KILL_* above) against dst/anchor;
    SIGKILL it the instant it reports readiness via stdout.

    The child prints "ready" and self-SIGSTOPs at its instrumented point,
    so the parent's blocking readline() is the synchronization -- no
    sleep, no timing race. SIGKILL still terminates a stopped process
    immediately (POSIX: SIGKILL can't be blocked, caught, or ignored).
    """
    proc = subprocess.Popen(
        [sys.executable, str(script), str(dst), str(anchor)],
        env={**os.environ, "PYTHONPATH": str(INCUBATOR_ROOT)},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert proc.stdout is not None
    line: str = proc.stdout.readline()  # pyright: ignore[reportAny]
    if line != "ready\n":
        # Child errored before its pause point (or was never reached) --
        # it has already exited, so draining stderr now is safe. Reading
        # stderr unconditionally here instead would deadlock: a child
        # that DID reach "ready" is merely SIGSTOPped, not exited, and
        # its stderr pipe never hits EOF until something kills it.
        _, stderr = proc.communicate(timeout=10)
        raise AssertionError(
            f"child never reached its pause point: {stderr!r} (stdout: {line!r})"
        )
    os.kill(proc.pid, signal.SIGKILL)
    returncode = proc.wait(timeout=10)
    assert returncode == -signal.SIGKILL, returncode


class DescribeKillMidFlight:
    """Real SIGKILL at each interruption point named in the requirement's
    verification (`030-requirements.kb/atomic-cache-updates.md`: "kill a
    sync mid-flight; the mount continues serving the previous content
    without errors") -- not the simulated-state tests above, an actual
    kill -9 against a real child process."""

    def it_recovers_from_a_kill_during_populate(self, tmp_path: Path):
        dst = tmp_path / "thing"
        _ = dst.write_text("old")

        kill_at_ready(CHILD_KILL_DURING_POPULATE, dst, tmp_path)

        # a reader mid-outage sees only the untouched previous content
        assert dst.read_text() == "old"
        assert sibling(dst, "tmp").read_text() == "half-written"

        recover(dst)
        assert dst.read_text() == "old"
        assert sibling(dst, "fail").read_text() == "half-written"
        assert not sibling(dst, "tmp").exists()

        # the next run heals with no manual cleanup and succeeds normally
        with staged(dst, anchor=tmp_path) as scratch:
            _ = scratch.write_text("new")
        assert dst.read_text() == "new"
        assert not sibling(dst, "fail").exists()

    def it_recovers_from_a_kill_between_the_two_renames(self, tmp_path: Path):
        dst = tmp_path / "thing"
        dst.mkdir()
        _ = (dst / "old_file").write_text("old")

        kill_at_ready(CHILD_KILL_BETWEEN_RENAMES, dst, tmp_path)

        # the syscall-width gap this fallback accepts: dst momentarily
        # absent, the complete old version parked at .old
        assert not dst.exists()
        assert (sibling(dst, "old") / "old_file").read_text() == "old"
        assert (sibling(dst, "tmp") / "new_file").read_text() == "new"

        recover(dst)
        assert (dst / "old_file").read_text() == "old"
        assert not sibling(dst, "old").exists()
        assert (sibling(dst, "fail") / "new_file").read_text() == "new"

    def it_recovers_from_a_kill_before_old_cleanup(self, tmp_path: Path):
        dst = tmp_path / "thing"
        dst.mkdir()
        _ = (dst / "old_file").write_text("old")

        kill_at_ready(CHILD_KILL_BEFORE_OLD_CLEANUP, dst, tmp_path)

        # already fully promoted -- readers see the new complete version
        assert (dst / "new_file").read_text() == "new"
        assert not (dst / "old_file").exists()
        assert (sibling(dst, "old") / "old_file").read_text() == "old"

        recover(dst)
        assert (dst / "new_file").read_text() == "new"
        assert not sibling(dst, "old").exists()
        assert not sibling(dst, "fail").exists()

    def it_survives_a_kill_during_post_exchange_cleanup(self, tmp_path: Path):
        dst = tmp_path / "thing"
        dst.mkdir()
        _ = (dst / "old_file1").write_text("old1")
        _ = (dst / "old_file2").write_text("old2")

        kill_at_ready(CHILD_KILL_DURING_EXCHANGE_CLEANUP, dst, tmp_path)

        # RENAME_EXCHANGE already committed atomically -- dst is fully new
        # regardless of the crash mid-cleanup that follows it
        assert (dst / "new_file").read_text() == "new"
        assert not (dst / "old_file1").exists()

        # the displaced old copy, mid-removal, is quarantined as the tmp
        assert sibling(dst, "tmp").is_dir()

        recover(dst)
        assert (dst / "new_file").read_text() == "new"
        assert sibling(dst, "fail").is_dir()  # the partially-removed old copy
        assert not sibling(dst, "tmp").exists()
