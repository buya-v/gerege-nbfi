#!/usr/bin/env python3
"""T179 RED FIXTURE (a2) — a REAL try/finally node, in the wrong place.

This is the failure a naive AST check would still make: an `ast.Try` with a
`finalbody` exists in this file, and `atexit.register` appears as a real call node —
but the finally guards a different function, and the registration sits in a function
nothing calls.  Neither is reachable from the mutation site.  Verdict: UNGUARDED.
"""
import atexit
import os

if __name__ == "__main__":
    raise SystemExit("t179 fixture: parsed, never run")

CAPTURE = ".softhouse/capture/t179-fixture-never-run/out.txt"


def unrelated_work():
    tmp = "/tmp/t179-unrelated"
    try:
        open(tmp, "w").write("x")
    finally:
        os.remove(tmp)


def never_called_registrar():
    atexit.register(lambda: None)


def clobber(text):
    # the mutation: unguarded, on a trusted artefact
    with open(CAPTURE, "w", encoding="utf-8") as fh:  # T179-SITE
        fh.write(text)
