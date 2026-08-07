import sys
from pathlib import Path

from chatfs.shell.locks import write_locked

with write_locked(Path(sys.argv[1])):
    print("ok")
