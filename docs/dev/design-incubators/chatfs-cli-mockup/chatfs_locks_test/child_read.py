import sys
from pathlib import Path

from chatfs_locks import read_locked

with read_locked(Path(sys.argv[1])):
    print("ok")
