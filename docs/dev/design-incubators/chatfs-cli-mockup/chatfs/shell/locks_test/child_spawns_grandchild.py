import sys
from pathlib import Path

from chatfs_locks import run, write_locked

anchor = Path(sys.argv[1])
grandchild = Path(__file__).parent / "child_reenter_w.py"
with write_locked(anchor):
    result = run([sys.executable, str(grandchild), str(anchor)], capture_output=True)
    _ = sys.stdout.buffer.write(result.stdout)
    _ = sys.stderr.buffer.write(result.stderr)
    sys.exit(result.returncode)
