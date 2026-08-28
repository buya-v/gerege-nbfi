#!/usr/bin/env python3
"""T321 part 1 -- THE RUNTIME PATH TRACER. Written to a scratch directory as `sitecustomize.py`
and put on PYTHONPATH, so it loads into EVERY python3 process an instrument starts, including
the ones a shell guard spawns, WITHOUT editing a single byte of any instrument.

WHY THIS EXISTS. T316's dead-path census matches STRING LITERALS. Its own Unverified says so:
"a path assembled at runtime from variables is NOT seen ... `os.path.join(BASE, name)` is
invisible to it, and that is likely where a real fail-open would hide." A regex cannot be
widened to cover that; the value only exists at run time. So the detection is moved to the only
place the assembled path is a fact: THE MOMENT IT IS USED.

WHAT IT RECORDS. Every path handed to `open`, `os.stat/lstat/access/listdir/scandir`,
`os.path.exists/isfile/isdir`, and the pathlib equivalents, plus every argv token of every
`subprocess` launch -- with, for each, WHETHER IT EXISTED AT THE MOMENT OF THE CALL. One
tab-separated row per touch, appended to $T321_TRACE_OUT.

WHAT IT CANNOT DO, said here rather than left for a reviewer to find:
  * it sees only the code paths that EXECUTE. A dependency behind an `if` that did not fire is
    invisible to it, exactly as a literal in a comment is invisible to a regex. The two methods
    are complementary and neither is a superset -- which is why the census and the trace are
    both reported and their DIFFERENCE is the interesting number.
  * a path opened by a NON-python, NON-traced child (a C program, `grep`, `git`) is seen only
    as an argv token, and only if it appears literally in argv.
  * `python3 -S` or `-E` disables site processing and therefore this tracer. The runner asserts
    the tracer loaded by requiring a self-test row, and REFUSES if it is absent -- a tracer that
    silently failed to load would report "no paths touched", which reads exactly like a clean
    result. That is the failure mode this whole task is about.
"""
import builtins
import os
import sys

_OUT = os.environ.get("T321_TRACE_OUT")
_REAL_OPEN = builtins.open          # captured BEFORE anything is patched
_FH = None
_N = 0
_CAP = 400000


def _log(kind, p):
    """Always writes through _REAL_OPEN. Routing the logger through the PATCHED open is an
    infinite recursion, and it is the first thing this file got wrong."""
    if not _OUT:
        return
    try:
        s = os.fspath(p)
    except Exception:
        return
    if isinstance(s, bytes):
        try:
            s = s.decode("utf-8", "replace")
        except Exception:
            return
    if not isinstance(s, str):
        return
    try:
        existed = "1" if os.path.lexists(s) else "0"
    except Exception:
        existed = "?"
    global _FH, _N
    if _N > _CAP:
        return
    try:
        if _FH is None:
            _FH = _REAL_OPEN(_OUT, "a", buffering=1 << 16)
            import atexit
            atexit.register(_close)
        _FH.write("%s\t%s\t%s\t%d\n" % (kind, existed, s, os.getpid()))
        _N += 1
    except Exception:
        pass


def _close():
    """The handle is HELD OPEN, not reopened per event. Opening, appending and closing the trace
    file on every stat() made a lint over 1266 files take ten minutes and turned this instrument
    into something nobody would run twice. O_APPEND makes the concurrent child writes safe.
    A per-process CAP exists so a pathological target cannot fill the disk; the cap is REPORTED
    by the runner if it is hit, never silently truncating into a smaller-looking result."""
    global _FH
    try:
        if _FH is not None:
            if _N > _CAP:
                _FH.write("cap-hit\t?\t%d\t%d\n" % (_N, os.getpid()))
            _FH.flush()
            _FH.close()
    except Exception:
        pass
    _FH = None


_log_safe = _log


if _OUT:
    def _open(file, *a, **k):
        _log("open", file)
        return _REAL_OPEN(file, *a, **k)

    builtins.open = _open

    _wrapped = [
        (os, "stat"), (os, "lstat"), (os, "access"), (os, "listdir"), (os, "scandir"),
        (os.path, "exists"), (os.path, "isfile"), (os.path, "isdir"), (os.path, "getsize"),
    ]
    for mod, name in _wrapped:
        _f = getattr(mod, name, None)
        if _f is None:
            continue

        def _mk(f, nm):
            def w(path, *a, **k):
                _log_safe(nm, path)
                return f(path, *a, **k)
            return w
        try:
            setattr(mod, name, _mk(_f, name))
        except Exception:
            pass

    try:
        import pathlib

        for nm in ("exists", "is_file", "is_dir", "open", "read_text", "read_bytes",
                   "iterdir", "stat", "write_text", "mkdir", "unlink"):
            _f = getattr(pathlib.Path, nm, None)
            if _f is None:
                continue

            def _mkp(f, name):
                def w(self, *a, **k):
                    _log_safe("Path." + name, str(self))
                    return f(self, *a, **k)
                return w
            try:
                setattr(pathlib.Path, nm, _mkp(_f, nm))
            except Exception:
                pass
    except Exception:
        pass

    try:
        import subprocess

        _real_popen_init = subprocess.Popen.__init__

        def _popen_init(self, args, *a, **k):
            try:
                seq = args if isinstance(args, (list, tuple)) else [args]
                for tok in seq:
                    if isinstance(tok, (str, bytes, os.PathLike)):
                        _log_safe("argv", tok)
            except Exception:
                pass
            return _real_popen_init(self, args, *a, **k)
        subprocess.Popen.__init__ = _popen_init
    except Exception:
        pass

    # SELF-TEST ROW. The runner REFUSES if this is missing, because "the tracer never loaded"
    # and "the instrument touched nothing" produce byte-identical output otherwise.
    _log_safe("tracer-loaded", sys.executable)
