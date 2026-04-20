# Standalone GUI Application

A dedicated desktop or web app displays conversations. Users browse, search,
and read through the app's UI rather than through the filesystem.

**Pros.** Rich presentation possible (fork visualization, inline media,
threaded views). No mount, no daemon — just a regular application.

**Cons.** Defeats the mission. `010-mission.kb/chatfs.md` is explicitly about
Unix composability: `grep`, `cat`, editors, pipes. A GUI replaces the very
toolchain the project exists to enable.

A GUI on top of a FUSE mount is perfectly fine — that's additive. A GUI
instead of a filesystem is not.
