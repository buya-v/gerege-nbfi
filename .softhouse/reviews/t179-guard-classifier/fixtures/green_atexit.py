#!/usr/bin/env python3
"""T179 GREEN FIXTURE (b2) — a live, module-scope atexit registration.

Weaker than try/finally, and reported as its own verdict GUARDED-PROCESS: the tool
proves a handler is registered and on a live path, never that the handler restores
this artefact.
"""
import atexit

if __name__ == "__main__":
    raise SystemExit("t179 fixture: parsed, never run")

RIG = ".softhouse/capture/t179-fixture-never-run/conformance.sh"
_ORIGINAL = None


def _restore():
    if _ORIGINAL is not None:
        open(RIG, "w", encoding="utf-8").write(_ORIGINAL)


atexit.register(_restore)


def patch(text):
    open(RIG, "w", encoding="utf-8").write(text)  # T179-SITE
