#!/usr/bin/env python3
"""T179 GREEN FIXTURE (b5) — the mutation lives in a helper whose EVERY in-file call
site sits inside a try/finally.  One interprocedural step, deliberately
conservative: a single unguarded call site would disqualify it."""
import shutil

if __name__ == "__main__":
    raise SystemExit("t179 fixture: parsed, never run")

STORE = ".softhouse/vectors/t179-fixture-never-run/case.json"


def _write(body):
    open(STORE, "w", encoding="utf-8").write(body)  # T179-SITE


def run(body):
    shutil.copyfile(STORE, STORE + ".bak")
    try:
        _write(body)
    finally:
        shutil.move(STORE + ".bak", STORE)
