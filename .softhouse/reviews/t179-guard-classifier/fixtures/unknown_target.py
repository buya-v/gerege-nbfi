#!/usr/bin/env python3
"""T179 FIXTURE (c) — a target this tool cannot resolve.  It must land in the
UNKNOWN scope and be PRINTED, never folded into 'clean'."""

if __name__ == "__main__":
    raise SystemExit("t179 fixture: parsed, never run")


def clobber(path_from_caller, body):
    open(path_from_caller, "w", encoding="utf-8").write(body)  # T179-SITE
