#!/usr/bin/env python3
"""T179 GREEN FIXTURE (b1) — genuinely guarded: backup, mutate, restore in finally.

The check must NOT be over-broad: this file must PASS (P-50 — a selftest that only
proves refusal proves half the instrument).
"""
import shutil

if __name__ == "__main__":
    raise SystemExit("t179 fixture: parsed, never run")

STORE = ".softhouse/vectors/t179-fixture-never-run/case.json"


def measure():
    return 0


def mutate_and_restore(body):
    backup = STORE + ".bak"
    shutil.copyfile(STORE, backup)
    try:
        with open(STORE, "w", encoding="utf-8") as fh:  # T179-SITE
            fh.write(body)
        return measure()
    finally:
        shutil.move(backup, STORE)
