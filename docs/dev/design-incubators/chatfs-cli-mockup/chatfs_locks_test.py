"""Lock-table tests: acquisition, eager registry<->env sync, borrow
(reentrancy without flock-conversion downgrade), seeding from an
inherited table, and cross-process re-entry through run()."""

import fcntl
import os
import subprocess
import sys
from pathlib import Path

import pytest

import chatfs_locks
from chatfs_locks import Lock, read_locked, registry, run, write_locked

HERE = Path(__file__).parent
ENV = chatfs_locks._ENV  # pyright: ignore[reportPrivateUsage]
seed = chatfs_locks._seed  # pyright: ignore[reportPrivateUsage]


@pytest.fixture(autouse=True)
def clean_slate(monkeypatch: pytest.MonkeyPatch):
    registry.clear()
    monkeypatch.delenv(ENV, raising=False)
    monkeypatch.setattr(chatfs_locks, "_seeded", True)  # seeding tests opt back in


def probe(anchor: Path, op: int) -> bool:
    """Can a fresh open-file-description take this flock right now?"""
    fd = os.open(anchor, os.O_RDONLY | os.O_DIRECTORY)
    try:
        try:
            fcntl.flock(fd, op | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        return True
    finally:
        os.close(fd)


def key(anchor: Path) -> tuple[int, int]:
    st = os.stat(anchor)
    return (st.st_dev, st.st_ino)


class DescribeAcquisition:
    def it_excludes_even_a_reader_under_a_write_lock(self, tmp_path: Path):
        with write_locked(tmp_path):
            assert not probe(tmp_path, fcntl.LOCK_SH)

    def it_admits_a_second_reader_under_a_read_lock(self, tmp_path: Path):
        with read_locked(tmp_path):
            assert probe(tmp_path, fcntl.LOCK_SH)

    def it_releases_and_unregisters_on_exit(self, tmp_path: Path):
        with write_locked(tmp_path):
            pass
        assert probe(tmp_path, fcntl.LOCK_EX)
        assert registry == {}
        assert ENV not in os.environ


class DescribeRegistryEnvSync:
    def it_publishes_each_acquisition_eagerly(self, tmp_path: Path):
        with write_locked(tmp_path):
            lock = registry[key(tmp_path)]
            assert lock.mode == "w" and lock.owned
            assert os.environ[ENV] == f"{lock.fd}:w"

    def it_lists_every_held_anchor(self, tmp_path: Path):
        a, b = tmp_path / "a", tmp_path / "b"
        a.mkdir()
        b.mkdir()
        with write_locked(a):
            with read_locked(b):
                entries = set(os.environ[ENV].split())
                assert entries == {
                    f"{registry[key(a)].fd}:w",
                    f"{registry[key(b)].fd}:r",
                }
            assert os.environ[ENV] == f"{registry[key(a)].fd}:w"


class DescribeBorrowing:
    def it_borrows_read_under_write_without_downgrading(self, tmp_path: Path):
        with write_locked(tmp_path):
            with read_locked(tmp_path):
                # a flock(LOCK_SH) here would CONVERT the held EX to SH;
                # exclusivity persisting proves no syscall was made
                assert not probe(tmp_path, fcntl.LOCK_SH)
            assert not probe(tmp_path, fcntl.LOCK_SH)  # inner exit: no release

    def it_borrows_write_under_write(self, tmp_path: Path):
        with write_locked(tmp_path):
            fd = registry[key(tmp_path)].fd
            with write_locked(tmp_path):
                assert registry[key(tmp_path)].fd == fd  # same OFD, no re-open
            assert not probe(tmp_path, fcntl.LOCK_SH)

    def it_refuses_upgrade_from_read_to_write(self, tmp_path: Path):
        with read_locked(tmp_path):
            with pytest.raises(AssertionError, match="no upgrade"):
                with write_locked(tmp_path):
                    pass
            assert probe(tmp_path, fcntl.LOCK_SH)  # still just the read lock


class DescribeSeeding:
    def _hold_and_publish(self, anchor: Path, mode: str, monkeypatch: pytest.MonkeyPatch) -> int:
        """Simulate the parent's half: a real flocked dir fd + env entry."""
        fd = os.open(anchor, os.O_RDONLY | os.O_DIRECTORY)
        fcntl.flock(fd, fcntl.LOCK_EX if mode == "w" else fcntl.LOCK_SH)
        monkeypatch.setenv(ENV, f"{fd}:{mode}")
        monkeypatch.setattr(chatfs_locks, "_seeded", False)
        return fd

    def it_adopts_an_inherited_fd_as_borrowed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        fd = self._hold_and_publish(tmp_path, "w", monkeypatch)
        seed()
        assert registry[key(tmp_path)] == Lock(fd, "w", owned=False)
        with write_locked(tmp_path):  # would deadlock if not borrowed
            assert not probe(tmp_path, fcntl.LOCK_SH)
        _ = os.fstat(fd)  # borrow exit must not have closed it
        os.close(fd)

    def it_warns_and_drops_a_closed_fd(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ):
        fd = self._hold_and_publish(tmp_path, "w", monkeypatch)
        os.close(fd)
        seed()
        assert registry == {}
        assert ENV not in os.environ  # stale entry dropped from serialized form too
        assert "not open" in capsys.readouterr().err

    def it_ignores_a_non_directory_fd(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ):
        plain = tmp_path / "plain"
        plain.touch()
        fd = os.open(plain, os.O_RDONLY)
        monkeypatch.setenv(ENV, f"{fd}:w")
        monkeypatch.setattr(chatfs_locks, "_seeded", False)
        seed()
        assert registry == {}
        assert "not a directory" in capsys.readouterr().err
        os.close(fd)


CHILDREN = HERE / "chatfs_locks_test"
CHILD_REENTER_W = CHILDREN / "child_reenter_w.py"
CHILD_READ = CHILDREN / "child_read.py"
CHILD_SPAWNS_GRANDCHILD = CHILDREN / "child_spawns_grandchild.py"


def child(
    script: Path, anchor: Path, *, via_run: bool = True, timeout: float = 10
) -> subprocess.CompletedProcess[bytes]:
    argv = [sys.executable, str(script), str(anchor)]
    env = {**os.environ, "PYTHONPATH": str(HERE)}
    if via_run:
        return run(argv, capture_output=True, timeout=timeout, env=env)
    return subprocess.run(argv, capture_output=True, timeout=timeout, env=env)


class DescribeSubprocessReentry:
    def it_reenters_the_parents_write_lock_without_deadlock(self, tmp_path: Path):
        with write_locked(tmp_path):
            result = child(CHILD_REENTER_W, tmp_path)
        assert result.returncode == 0, result.stderr
        assert result.stdout == b"ok\n"

    def it_keeps_the_parent_exclusive_after_a_child_read(self, tmp_path: Path):
        with write_locked(tmp_path):
            result = child(CHILD_READ, tmp_path)
            assert result.returncode == 0, result.stderr
            assert not probe(tmp_path, fcntl.LOCK_SH)  # child's borrow didn't downgrade

    def it_warns_but_succeeds_when_spawned_without_fd_inheritance(self, tmp_path: Path):
        # parent holds r; the child's env table names a dead fd, so it
        # warns and acquires fresh -- SH beside SH, so no hang to manage.
        with read_locked(tmp_path):
            result = child(CHILD_READ, tmp_path, via_run=False)
        assert result.returncode == 0, result.stderr
        assert result.stdout == b"ok\n"
        assert b"not open" in result.stderr

    def it_blocks_a_second_writer_from_an_unrelated_process_tree(self, tmp_path: Path):
        with write_locked(tmp_path):
            env = {**os.environ, "PYTHONPATH": str(HERE)}
            proc = subprocess.Popen(
                [sys.executable, str(CHILD_REENTER_W), str(tmp_path)],
                env=env,  # unrelated tree: no pass_fds, so the inherited
                # __CHATFS_LOCKS entry (if any survives env-copy) names a
                # dead fd -- the child must genuinely re-flock and block
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            with pytest.raises(subprocess.TimeoutExpired):
                _ = proc.wait(timeout=0.5)  # blocked on the kernel lock, not crashed
        # write lock released above; the child's flock can now proceed
        stdout, stderr = proc.communicate(timeout=10)
        assert proc.returncode == 0, stderr
        assert stdout == b"ok\n"
        assert b"not open" in stderr  # dead fd from the copied-but-unshared env entry

    def it_survives_a_grandchild_two_execs_deep(self, tmp_path: Path):
        with write_locked(tmp_path):
            result = child(CHILD_SPAWNS_GRANDCHILD, tmp_path)
        assert result.returncode == 0, result.stderr
        assert result.stdout == b"ok\n"
