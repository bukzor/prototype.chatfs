# Explicit CLI Commands

Custom commands (`chatfs-ls`, `chatfs-cat`, `chatfs-sync`, etc.) handle both
sync and read operations. Users invoke these commands rather than using
standard filesystem tools.

**Pros.** No FUSE daemon, no kernel module, no mount management. Fewer
moving parts at startup; simpler to debug.

**Cons.** Users must learn and remember chatfs-specific commands for every
operation. Editors, file managers, IDEs, file watchers, and every other tool
that opens files by path doesn't work without custom integration. Shell
completion, glob expansion, and piping between standard tools requires
bespoke support in each chatfs command.

Earlier design iterations chose this over FUSE under the belief that FUSE was
too heavy. In practice, userspace FUSE is routine on Linux and the
unmodified-standard-tools win is decisive for the mission
(`010-mission.kb/chatfs.md`).
