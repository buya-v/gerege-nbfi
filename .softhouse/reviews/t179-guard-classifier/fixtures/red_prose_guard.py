#!/usr/bin/env python3
"""T179 RED FIXTURE (a) — shape (a) of the P-48 defect, in miniature.

This file mutates an artefact a later reader trusts and has NO handler on ANY exit
path.  The words `trap` and `finally` appear below only inside string literals this
script would WRITE INTO another document — exactly as
`.softhouse/reviews/t47-probe/t47_edit_1.py` does.

T156's GUARD regex scores this file GUARDED.  The parser must score it UNGUARDED.
Never executed; parsed only.
"""
import sys

if __name__ == "__main__":
    raise SystemExit("t179 fixture: parsed, never run")

STORE = ".softhouse/vectors/t179-fixture-never-run/case.json"

ADR_PROSE = (
    "One trap worth naming: a rig that mutates the store and restores it with a\n"
    "plain statement rather than a trap that runs on every exit path.\n"
)
SECOND_PARAGRAPH = "The finally: clause is the shape we want here, not an assert.\n"


def rewrite(body):
    # in-place, truncating, no handler anywhere on this path
    fh = open(STORE, "w", encoding="utf-8")  # T179-SITE
    fh.write(body + ADR_PROSE + SECOND_PARAGRAPH)
    fh.close()
    return 0


def run():
    return rewrite(sys.argv[1] if len(sys.argv) > 1 else "")
