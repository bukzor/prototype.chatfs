import sys
from pathlib import Path

from chatfs.shell.locks import read_locked

with read_locked(Path(sys.argv[1])):
    print("ok")
