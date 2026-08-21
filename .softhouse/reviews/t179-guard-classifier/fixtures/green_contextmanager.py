#!/usr/bin/env python3
"""T179 GREEN FIXTURE (b3) — a locally defined restoring context manager."""
import contextlib
import os
import shutil

if __name__ == "__main__":
    raise SystemExit("t179 fixture: parsed, never run")

PORT = "nexus/internal/schedule/contract.go"


@contextlib.contextmanager
def preserved(path):
    bak = path + ".t179bak"
    shutil.copyfile(path, bak)
    try:
        yield path
    finally:
        os.replace(bak, path)


def patch_port(text):
    with preserved(PORT):
        open(PORT, "w", encoding="utf-8").write(text)  # T179-SITE
