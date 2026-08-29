"""
T477 -- THE ENVIRONMENT HIJACK.  IT PROVES AN ABSOLUTE INTERPRETER PATH IS NOT SUFFICIENT.

`site` is imported during interpreter start-up and imports `sitecustomize` from `sys.path`,
and `PYTHONPATH` is on `sys.path`.  So a directory on `PYTHONPATH` holding this file runs
ATTACKER CODE INSIDE /usr/bin/python3, BEFORE the `-c` program text, with no shim on PATH and
no write access to any system directory.  Resolving the interpreter absolutely closes the PATH
route and does nothing about this one.

It fires only for the whole-tree recompute (`-c` in argv, and a repository under the cwd), so
every other python this bar runs is untouched and the arm measures one thing.  When it fires it
prints the same fabricated census the echo shim prints and exits before the real program runs.

`-E` / `-I` (PYTHONPATH ignored) and `-S` (site not imported at all) each close it; the fix
ships both.
"""
import os
import subprocess
import sys


def _fire():
    if "-c" not in sys.argv:
        return
    selfrel = os.environ.get("T477_SELFREL", "")
    if not selfrel:
        return
    delim = b"\x00" if os.environ.get("T477_SHIM_D", "nl") == "nul" else b"\n"
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD:" + selfrel]).strip()
        disk = subprocess.check_output(
            ["git", "hash-object", "--no-filters", "--", selfrel]).strip()
    except Exception:
        return
    log = os.environ.get("T477_SHIM_LOG", "")
    if log:
        with open(log, "ab") as fh:
            fh.write(b"sitecustomize fired inside /usr/bin/python3: " + head + b" " + disk
                     + b"\n")
    # It is handed the listing on stdin; drain it and count the records, exactly as the echo
    # shim does, so the SCANNED figure it fabricates is the one the caller expects.
    try:
        n = sys.stdin.buffer.read().count(b"\x00")
    except Exception:
        n = 0
    out = sys.stdout.buffer
    out.write(b"CALIB " + head + b" " + disk + delim)
    out.write(b"SCANNED " + str(n).encode() + delim)
    out.flush()
    os._exit(0)


_fire()
