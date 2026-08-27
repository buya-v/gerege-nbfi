#!/usr/bin/env python3
"""T205 FIXTURE (e) — THE POLARITY GUARD ON T205'S OWN FIX.

The fix consults a TRANSITIVE fragment closure when the ordinary probe says UNKNOWN.
That closure is new evidence, and new evidence that could say SCRATCH would be a
FAIL-OPEN — it would let a runtime-derived `/tmp` fragment EXCUSE a write, which is
the exact failure direction this task exists to close.  So a chain probe returning
SCRATCH is DISCARDED and the site stays UNKNOWN.

This fixture is the vehicle for that assertion.  `dest` is unresolvable by design
(it comes from a call this tool does not follow), so:
  * classified as-is it must be UNKNOWN/UNGUARDED — never SANDBOX;
  * classified with a SCRATCH entry INJECTED into the resolver's chain map by the
    selftest, it must STILL be UNKNOWN/UNGUARDED.
The second arm is white-box on purpose: no ordinary source shape reaches the discard
branch, because the pre-existing scratch propagation already dominates it, and a
branch that is never driven is not a proven branch.
"""
import os

if __name__ == "__main__":
    raise SystemExit("t205 fixture: parsed, never run")


def where(tag):
    return os.path.join(tag)


def clobber(tag, body):
    dest = where(tag)
    open(dest, "w", encoding="utf-8").write(body)                  # T179-SITE
