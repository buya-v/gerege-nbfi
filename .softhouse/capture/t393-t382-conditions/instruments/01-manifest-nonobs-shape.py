#!/usr/bin/env python3
"""T393 — SHAPE MEASUREMENT, not a guard: how far can a manifest arm reach?

Before widening section 10 I measure what the CURRENT MANIFEST.sha256 actually covers
outside out/ and req/, so the arm I write is sized to the measurement and not to a hope.
Printing only. No verdict, no exit code other than 0/2 — it decides nothing.
"""
import hashlib
import os
import pathlib
import subprocess
import sys

ROOT = os.environ.get("A2_11_ROOT") or str(pathlib.Path(__file__).resolve().parents[4])
CAPREL = ".softhouse/capture/tierA-a2"
OBS_DIRS = ("out", "req")
MANREL = CAPREL + "/MANIFEST.sha256"


def g(*args):
    r = subprocess.run(["git", "-C", ROOT, *args], capture_output=True)
    if r.returncode != 0:
        print("REFUSED  git %s exited %d" % (" ".join(args), r.returncode))
        sys.exit(2)
    return r.stdout


man = {}
for line in open(os.path.join(ROOT, MANREL), "rb").read().decode().split("\n"):
    line = line.rstrip()
    if not line or line.startswith("#"):
        continue
    parts = line.split(None, 1)
    if len(parts) == 2:
        man[parts[1].lstrip("*").strip()] = parts[0]

tracked = set()
for line in g("ls-tree", "-r", "--name-only", "HEAD", "--", CAPREL).decode().split("\n"):
    line = line.strip()
    if line.startswith(CAPREL + "/"):
        tracked.add(line[len(CAPREL) + 1:])

non_obs_rows = sorted(k for k in man if k.split("/")[0] not in OBS_DIRS)
tracked_non_obs = sorted(k for k in tracked if k.split("/")[0] not in OBS_DIRS)

print("manifest rows total                    : %d" % len(man))
print("manifest rows outside out/ req/        : %d" % len(non_obs_rows))
print("tracked files under the capture dir    : %d" % len(tracked))
print("tracked files outside out/ req/        : %d" % len(tracked_non_obs))
print("manifest non-obs rows naming no tracked file: %s"
      % sorted(set(non_obs_rows) - tracked))
print("tracked non-obs files with NO manifest row  : %d" % len(set(tracked_non_obs) - set(man)))
for n in sorted(set(tracked_non_obs) - set(man)):
    print("    " + n)

agree = disagree = unreadable = 0
dis_names = []
for name in non_obs_rows:
    try:
        with open(os.path.join(ROOT, CAPREL, name), "rb") as fh:
            body = fh.read()
    except OSError:
        unreadable += 1
        continue
    if hashlib.sha256(body).hexdigest() == man[name]:
        agree += 1
    else:
        disagree += 1
        dis_names.append(name)
print()
print("non-obs manifest rows: digest AGREES with disk : %d" % agree)
print("non-obs manifest rows: digest DISAGREES        : %d %s" % (disagree, dis_names))
print("non-obs manifest rows: unreadable              : %d" % unreadable)

print()
print("--- disk walk under out/ and req/: anything not tracked, or not a regular file? ---")
untracked = []
nonregular = []
disk_count = 0
for d in OBS_DIRS:
    base = os.path.join(ROOT, CAPREL, d)
    for dirpath, dirnames, filenames in os.walk(base):
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, os.path.join(ROOT, CAPREL))
            disk_count += 1
            if rel not in tracked:
                untracked.append(rel)
            if os.path.islink(full):
                nonregular.append(rel)
print("files on disk under out/ + req/        : %d" % disk_count)
print("of those NOT tracked at HEAD           : %d %s" % (len(untracked), untracked[:10]))
print("of those that are SYMLINKS             : %d %s" % (len(nonregular), nonregular[:10]))
sys.exit(0)
