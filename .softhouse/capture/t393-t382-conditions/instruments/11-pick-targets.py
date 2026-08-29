#!/usr/bin/env python3
"""T393 — pick the mutation targets BY MEASUREMENT, so the drive carries no path literal.

Prints exactly three lines, each `KEY<TAB>capture-relative path`:
    FORKOBS    an observation that EXISTED at the fork sha        (ARM A can see it)
    POSTFORK   an observation captured AFTER the fork sha         (ARM A cannot see it)
    NONOBS     a fork-sha manifest entry outside out/ and req/    (ARM E's population)

Deterministic: the sorted-first member of each set. Chosen this way rather than typed so
that the drive script contains no repo path literal that could rot into a dead path, and so
the choice is re-derivable from the repository instead of from a transcript.

REFUSES (exit 2) if any of the three sets is empty — an empty set here would silently turn a
mutation case into a no-op, which is the vacuous pass this whole review is about.
"""
import os
import pathlib
import subprocess
import sys

ROOT = os.environ.get("A2_11_ROOT") or str(pathlib.Path(__file__).resolve().parents[4])
CAPREL = ".softhouse/capture/tierA-a2"
OBS_DIRS = ("out", "req")
FORK = "12a7f8d9a3af4665fd5281a9f9c001d4f1276a53"
MANREL = CAPREL + "/MANIFEST.sha256"


def g(*args):
    r = subprocess.run(["git", "-C", ROOT, *args], capture_output=True)
    if r.returncode != 0:
        sys.stderr.write("REFUSED: git %s exited %d\n" % (" ".join(args), r.returncode))
        sys.exit(2)
    return r.stdout


def obs(ref):
    out = []
    for line in g("ls-tree", "-r", "--name-only", ref, "--", CAPREL).decode().split("\n"):
        line = line.strip()
        if line.startswith(CAPREL + "/"):
            rel = line[len(CAPREL) + 1:]
            if rel.split("/")[0] in OBS_DIRS:
                out.append(rel)
    return sorted(out)


fork_obs = obs(FORK)
head_obs = obs("HEAD")
post = sorted(set(head_obs) - set(fork_obs))

non_obs = []
for line in g("show", FORK + ":" + MANREL).decode().split("\n"):
    line = line.rstrip()
    if not line or line.startswith("#"):
        continue
    parts = line.split(None, 1)
    if len(parts) == 2:
        name = parts[1].lstrip("*").strip()
        if name.split("/")[0] not in OBS_DIRS:
            non_obs.append(name)
non_obs.sort()

if not fork_obs or not post or not non_obs:
    sys.stderr.write("REFUSED: empty target set fork=%d post=%d nonobs=%d\n"
                     % (len(fork_obs), len(post), len(non_obs)))
    sys.exit(2)

print("FORKOBS\t" + fork_obs[0])
print("POSTFORK\t" + post[0])
# manifest.py is the file T382 drove FINDING 3 on: the script that WRITES the manifest.
# Prefer it when present so this drive reproduces T382's case exactly; otherwise take the
# sorted-first member, and say which was used.
print("NONOBS\t" + ("manifest.py" if "manifest.py" in non_obs else non_obs[0]))
sys.exit(0)
