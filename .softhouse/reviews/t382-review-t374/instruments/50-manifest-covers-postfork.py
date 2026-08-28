#!/usr/bin/env python3
"""T382 — T374's follow-up #1 says closing the post-fork gap "needs a pinned per-file digest
list, which is a NEW evidence artefact rather than a repair". This measures whether that is
true, by running rather than arguing.

MEASURED HERE, on the T374 merge result:
  * how many of the 1035 tracked observations under capture/tierA-a2/{out,req}/ already have
    a row in the TRACKED file capture/tierA-a2/MANIFEST.sha256;
  * whether those recorded digests agree with the bytes on disk today;
  * whether the manifest's out/req row-set is EXACTLY the tracked out/req path-set — which is
    what would catch a committed DELETION or a fabricated ADDITION, the two cases T382's
    attack matrix found outside both of section 10's arms and outside T374's disclosure.

No floating point (P-25): counts from len() and sha256 hex digests only.
Usage: python3 50-manifest-covers-postfork.py <repo-root>
"""
import hashlib
import os
import subprocess
import sys

ROOT = sys.argv[1]
CAP = ".softhouse/capture/tierA-a2"
FORK = "12a7f8d9a3af4665fd5281a9f9c001d4f1276a53"


def git(*a):
    return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, check=True).stdout


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


tracked = sorted(
    p for p in git("ls-files", CAP + "/out", CAP + "/req").decode().split("\n") if p)
tracked_names = {p[len(CAP) + 1:] for p in tracked}
fork_paths = {p for p in git("ls-tree", "-r", "--name-only", FORK, "--",
                             CAP + "/out", CAP + "/req").decode().split("\n") if p}
postfork_names = {p[len(CAP) + 1:] for p in (set(tracked) - fork_paths)}

man = parse_manifest(open(os.path.join(ROOT, CAP, "MANIFEST.sha256"), "rb").read())
man_obs = {k: v for k, v in man.items() if k.startswith("out/") or k.startswith("req/")}

print("tracked observations under out/ + req/      : %d" % len(tracked_names))
print("  of which POST-FORK (arm A is blind to them): %d" % len(postfork_names))
print("MANIFEST.sha256 total rows                   : %d" % len(man))
print("  of which out/ or req/ rows                 : %d" % len(man_obs))
print()

missing_from_manifest = sorted(tracked_names - set(man_obs))
extra_in_manifest = sorted(set(man_obs) - tracked_names)
print("tracked observations with NO manifest row    : %d %s"
      % (len(missing_from_manifest), missing_from_manifest[:5]))
print("manifest rows naming NO tracked observation  : %d %s"
      % (len(extra_in_manifest), extra_in_manifest[:5]))

agree = disagree = unreadable = 0
bad = []
for name in sorted(man_obs):
    try:
        with open(os.path.join(ROOT, CAP, name), "rb") as fh:
            h = hashlib.sha256(fh.read()).hexdigest()
    except OSError as exc:
        unreadable += 1
        bad.append((name, "UNREADABLE " + repr(exc)))
        continue
    if h == man_obs[name]:
        agree += 1
    else:
        disagree += 1
        bad.append((name, "manifest=%s disk=%s" % (man_obs[name], h)))

print()
print("manifest digest vs disk, over out/ + req/    :")
print("  agree      : %d" % agree)
print("  DISAGREE   : %d" % disagree)
print("  unreadable : %d" % unreadable)
for n, d in bad[:10]:
    print("    %s  %s" % (n, d))

print()
postfork_covered = len(postfork_names & set(man_obs))
print("POST-FORK observations covered by a manifest row: %d of %d"
      % (postfork_covered, len(postfork_names)))
print()
if (not missing_from_manifest and not extra_in_manifest and disagree == 0
        and unreadable == 0 and postfork_covered == len(postfork_names)):
    print("RESULT: the tracked MANIFEST.sha256 ALREADY IS a pinned per-file digest list over")
    print("        every one of the %d tracked observations, its row-set is EXACTLY the tracked"
          % len(tracked_names))
    print("        path-set, and every digest agrees with disk. T374's follow-up #1 calls the")
    print("        closing artefact 'a NEW evidence artefact'; it is not new. A third arm in")
    print("        verify-capture-integrity.py reading this file would close the committed-")
    print("        deletion and fabricated-addition cases outright (set equality) and raise")
    print("        the bar on committed mutation to 'mutate the observation AND the manifest'.")
    sys.exit(0)
print("RESULT: the manifest does NOT currently cover the corpus exactly — see the figures above.")
sys.exit(1)
