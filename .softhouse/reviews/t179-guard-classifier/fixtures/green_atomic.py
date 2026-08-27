#!/usr/bin/env python3
"""T179 GREEN FIXTURE (b4) — atomic replace, which needs no handler at all
(P-48 rule 4).  Verdict must be ATOMIC, not UNGUARDED."""
import os
import tempfile

if __name__ == "__main__":
    raise SystemExit("t179 fixture: parsed, never run")

ADR = "docs/adr/DEC-1-schedule-generator-adapter.md"


def rewrite(body):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(ADR))
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(body)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, ADR)  # T179-SITE
