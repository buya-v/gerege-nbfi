#!/usr/bin/env python3
"""T393 — RE-VERIFY T382's F-2 counts INDEPENDENTLY, before relying on any of them.

T382's FINDING 2 asserts that `.softhouse/capture/tierA-a2/MANIFEST.sha256` already covers
exactly the tracked observation set, so a third arm reading it closes F-1's deletion,
addition and untracked cases without a new artefact. The coordinator's instruction is
explicit: VERIFY THOSE COUNTS YOURSELF. This file does that from the repository, with its
own enumeration, and REFUSES rather than printing a reassuring sentence if it cannot.

P-25: no floating point. Only len() counts and sha256 hex digests.
P-24: the historical baseline is a LITERAL immutable sha.

EXIT 0 every number T382 reports reproduces.  EXIT 1 at least one does not.
EXIT 2 REFUSED — could not measure.
"""
import hashlib
import os
import pathlib
import subprocess
import sys

ROOT = os.environ.get("A2_11_ROOT") or str(pathlib.Path(__file__).resolve().parents[4])
CAPREL = ".softhouse/capture/tierA-a2"
OBS_DIRS = ("out", "req")
FORK = "12a7f8d9a3af4665fd5281a9f9c001d4f1276a53"
MANREL = CAPREL + "/MANIFEST.sha256"

fails = []


def check(label, got, want):
    ok = got == want
    print(("  PASS  " if ok else "  FAIL  ") + "%-58s got=%s  T382=%s" % (label, got, want))
    if not ok:
        fails.append(label)


def g(*args):
    r = subprocess.run(["git", "-C", ROOT, *args], capture_output=True)
    if r.returncode != 0:
        print("  REFUSED  git %s exited %d: %s" % (" ".join(args), r.returncode,
                                                   r.stderr.decode()[:200]))
        sys.exit(2)
    return r.stdout


def tree(ref):
    return [l.strip() for l in g("ls-tree", "-r", "--name-only", ref, "--", CAPREL)
            .decode().split("\n") if l.strip()]


def is_obs(p):
    return p.startswith(CAPREL + "/") and p[len(CAPREL) + 1:].split("/")[0] in OBS_DIRS


def parse_manifest(blob):
    out = {}
    for line in blob.decode("utf-8").split("\n"):
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        out[parts[1].lstrip("*").strip()] = parts[0]
    return out


fork_all = tree(FORK)
head_all = tree("HEAD")
fork_obs = sorted(p for p in fork_all if is_obs(p))
head_obs = sorted(p for p in head_all if is_obs(p))
post_fork = sorted(set(head_obs) - set(fork_obs))

print("=== populations (T382 out/POPULATIONS.txt: 403 / 1035 / 632) ===")
check("observations tracked at the fork sha (ARM A population)", len(fork_obs), 403)
check("observations tracked at HEAD (ARM B population)", len(head_obs), 1035)
check("post-fork observations (in ARM B, invisible to ARM A)", len(post_fork), 632)

print()
print("=== MANIFEST.sha256 coverage (T382 out/MANIFEST-COVERAGE.txt) ===")
man = parse_manifest(open(os.path.join(ROOT, MANREL), "rb").read())
man_obs = {k: v for k, v in man.items() if k.split("/")[0] in OBS_DIRS}
tracked_rel = set(p[len(CAPREL) + 1:] for p in head_obs)
check("MANIFEST.sha256 total rows", len(man), 1139)
check("of which out/ or req/ rows", len(man_obs), 1035)
check("tracked observations with NO manifest row", len(tracked_rel - set(man_obs)), 0)
check("manifest rows naming NO tracked observation", len(set(man_obs) - tracked_rel), 0)

agree = disagree = unreadable = 0
for name, digest in sorted(man_obs.items()):
    try:
        with open(os.path.join(ROOT, CAPREL, name), "rb") as fh:
            body = fh.read()
    except OSError:
        unreadable += 1
        continue
    if hashlib.sha256(body).hexdigest() == digest:
        agree += 1
    else:
        disagree += 1
check("manifest digest vs disk: AGREE", agree, 1035)
check("manifest digest vs disk: DISAGREE", disagree, 0)
check("manifest digest vs disk: unreadable", unreadable, 0)
check("POST-FORK observations covered by a manifest row",
      sum(1 for p in post_fork if p[len(CAPREL) + 1:] in man_obs), 632)

print()
print("=== the fork-sha manifest, section 4's population (T382 FINDING 3: 430 / 403 / 27) ===")
old = parse_manifest(g("show", FORK + ":" + MANREL))
old_obs = [k for k in old if k.split("/")[0] in OBS_DIRS]
old_non = sorted(k for k in old if k.split("/")[0] not in OBS_DIRS)
check("entries in the fork-sha manifest", len(old), 430)
check("of those under out/ or req/ (section 10 covers these)", len(old_obs), 403)
check("NOT under out/ or req/ (section 4 ONLY — the saturated set)", len(old_non), 27)
print("      the 27, enumerated:")
for name in old_non:
    print("        " + name)

print()
print("=== which of the 27 are NOT byte-identical to the fork sha today ===")
print("    T382 / section 4's banner name exactly two: CAPTURE-PLAN.md and cap.sh.")
differ = []
same = 0
for name in old_non:
    rel = CAPREL + "/" + name
    at_fork = g("show", FORK + ":" + rel)
    try:
        with open(os.path.join(ROOT, rel), "rb") as fh:
            today = fh.read()
    except OSError as exc:
        print("  REFUSED  %s is missing on disk: %r" % (name, exc))
        sys.exit(2)
    if hashlib.sha256(at_fork).hexdigest() == hashlib.sha256(today).hexdigest():
        same += 1
    else:
        differ.append(name)
        print("        DIFFERS  %s\n                 fork  %s\n                 today %s"
              % (name, hashlib.sha256(at_fork).hexdigest(),
                 hashlib.sha256(today).hexdigest()))
check("of the 27 non-observation fork-sha entries, byte-identical", same, 25)
check("the differing set is exactly {CAPTURE-PLAN.md, cap.sh}",
      differ, ["CAPTURE-PLAN.md", "cap.sh"])

print()
print("FAILURES: %d" % len(fails))
for f in fails:
    print("  - " + f)
if fails:
    print()
    print("VERDICT: FAIL (exit 1) — a number T382 reports did NOT reproduce here. Do not build")
    print("on T382's FINDING 2 until the disagreement is explained.")
    sys.exit(1)
print()
print("VERDICT: PASS (exit 0) — every count T382 reports reproduces from an independent")
print("enumeration. MANIFEST.sha256's out/req row-set IS the tracked observation path-set.")
sys.exit(0)
