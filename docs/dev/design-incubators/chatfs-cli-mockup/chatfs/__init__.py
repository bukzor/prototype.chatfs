"""Every function outside main() is pure: no I/O, no side effects.

main() may import os/sys/subprocess/etc., inline, never at module top
level. Exception: the shell/ subpackage.
"""
