#!/usr/bin/env python3
"""T205 FIXTURE (d) — THE RUNTIME-COMPUTED-CONSTANT FAIL-OPEN, T203's F-2.

This is `T57-promote-emi-vectors.py` / `.softhouse/handoff/T8-promote-vectors.py`
reduced to their skeleton, and nothing about the write is disguised: it truncates a
file in the LIVE golden vector store with no handler on any exit path.

BEFORE T205 this scored scope UNKNOWN, so `--enforce` exited 0 on it — while the
otherwise identical `T74/T61/T64/T58` shape, whose store path is a plain module
constant that RESOLVES, scored TRUSTED and tripped `--enforce`.  The only difference
between the two is the `os.path.join(ROOT, …)` on the line below.

MUST NOW BE: verdict UNGUARDED, scope TRUSTED, tags include STORE.
"""
import json
import os

if __name__ == "__main__":
    raise SystemExit("t205 fixture: parsed, never run")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", ".."))
OUT = os.path.join(ROOT, ".softhouse", "vectors", "loanschedule")

SLUG = {"P-00": "P-00-baseline-6x7pct"}


def promote(case_id, vector):
    path = os.path.join(OUT, SLUG[case_id] + ".json")
    with open(path, "w") as fh:                                    # T179-SITE
        json.dump(vector, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
