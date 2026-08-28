#!/usr/bin/env python3
"""A2-11 (e) — verify A2-7's manifest claim WITHOUT trusting either manifest.

A2-7 claims: 430 entries before, 571 after, `verify` exit 0 at both ends, and all 430
pre-existing hashes byte-identical, proven by `prove-a2-7-additive.py` against the
LITERAL fork sha 12a7f8d9.

That prover compares MANIFEST FILE against MANIFEST FILE. Both are written by the same
script, so a laundered hash that was recorded consistently in both would survive. This
one does not read the new manifest's hash values at all: it RECOMPUTES the sha256 of
every pre-existing file from the git blob at the literal fork sha AND from the bytes on
disk today, and compares those two directly.

P-40: it counts what it skipped and names it. There is no bare `except: continue`.
P-24: the baseline is a literal immutable sha, never `git merge-base main HEAD`.
"""
import os
import pathlib
import hashlib
import subprocess
import sys

# T357 REPAIR -- was a hard-coded absolute path into the worktree
#   /Users/buv/gerege-nbfi/.claude/worktrees/agent-a3ac3d56d665ff7da
# which was RETIRED, so this script aborted with a traceback in every later checkout
# and the committed transcript stopped being re-derivable from the script that made
# it. Derived from __file__ instead: this file sits three levels below the checkout
# root, under reviews/A2-11, so parents[3] IS that root. In the ORIGINAL worktree it
# resolved to agent-a3ac3d56d665ff7da, so the substitution is OUTPUT-NEUTRAL there --
# it restores the evidence rather than altering it, and that claim is MEASURED in
# .softhouse/capture/t357-a2-11-section1-red/ (BEFORE/AFTER, and a diff against the
# committed transcript), not asserted. A2_11_ROOT overrides for a cross-checkout run.
ROOT = os.environ.get("A2_11_ROOT") or str(pathlib.Path(__file__).resolve().parents[3])
CAPREL = ".softhouse/capture/tierA-a2"
FORK = "12a7f8d9a3af4665fd5281a9f9c001d4f1276a53"   # LITERAL, not merge-base (P-24)

# T374 REPAIR (T362 F-6) -- was the LOCAL branch name softhouse/A2-7-capture-mandatory-accounts.
# A local-only ref is NOT clone-portable. T362 hit this for real: in a fresh clone only
# origin/softhouse/A2-7-capture-mandatory-accounts exists, every `git` call naming the bare
# branch raised CalledProcessError ... exit status 128, this script aborted with a traceback,
# and -- because T357 had just made the aggregate verdict real -- run-all.sh went to exit 1.
# T374 reproduced that in a fresh clone before repairing it (P-22); evidence in
# .softhouse/capture/t374-t362-conditions/out/10-F6-RED-fresh-clone-no-local-ref.txt.
#
# THIS FIRE ALREADY LOST A REVIEW TO EXACTLY THIS: softhouse/T361-review-t353 was absent both
# locally and on origin, and the only durable spelling turned out to be a commit-ish reachable
# from origin/main. So the branch NAME is replaced by the LITERAL sha of its head, which is
# reachable from origin/main and therefore survives a fresh clone. It is also more P-24
# correct than the name it replaces: an immutable sha cannot be moved by a later push.
#   $ git rev-parse softhouse/A2-7-capture-mandatory-accounts
#   b3f2d9b26c347c31fae17a835b458e6b0485d710
#   $ git merge-base --is-ancestor b3f2d9b2 origin/main && echo REACHABLE   -> REACHABLE
# Section 0 asserts that reachability rather than assuming it, so a checkout where the object
# is genuinely absent REFUSES by name instead of aborting on a traceback.
A2_7_HEAD = "b3f2d9b26c347c31fae17a835b458e6b0485d710"
MANIFEST = CAPREL + "/MANIFEST.sha256"
fails = []


def check(label, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + label + (("\n          " + detail) if detail else ""))
    if not cond:
        fails.append(label)


def git(*args):
    return subprocess.run(["git", "-C", ROOT, *args], capture_output=True, check=True).stdout


def parse_manifest(blob):
    out = {}
    for line in blob.decode("utf-8").split("\n"):
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        h, name = parts
        out[name.lstrip("*").strip()] = h
    return out


print("=== 0. the baseline is a LITERAL sha, and it is A2-7's real fork point (P-24) ===")
src = open(ROOT + "/" + CAPREL + "/prove-a2-7-additive.py").read()
check("prove-a2-7-additive.py hard-codes the literal sha",
      'BASELINE = "%s"' % FORK in src)
check("prove-a2-7-additive.py contains NO `git merge-base` anywhere",
      "merge-base" not in src.replace("`git merge-base main HEAD` resolves to", ""),
      "the only occurrence is the comment explaining why it is NOT used")
# T374 / T362 F-6: both commit-ishes must be PRESENT before anything is asked of them, or a
# clone missing an object reports a traceback where it should report a refusal.
have = subprocess.run(["git", "-C", ROOT, "cat-file", "-e", A2_7_HEAD + "^{commit}"],
                      capture_output=True).returncode == 0
check("A2-7's head %s is present in this checkout (it is reachable from "
      "origin/main, so a fresh clone has it; the BRANCH NAME it replaced was local-only "
      "and a fresh clone did NOT)" % A2_7_HEAD[:12], have)
if not have:
    print("  REFUSED  without that object nothing below can be measured. Stopping here rather")
    print("           than aborting on a traceback three arms later.")
    print()
    print("FAILURES: %d" % len(fails))
    for f in fails:
        print("  - " + f)
    sys.exit(1)
anc = subprocess.run(["git", "-C", ROOT, "merge-base", "--is-ancestor", FORK, A2_7_HEAD])
check("the literal sha is a genuine ancestor of A2-7's head", anc.returncode == 0)
on_branch = git("rev-list", "--count", FORK + ".." + A2_7_HEAD).decode().strip()
check("A2-7's head carries exactly 2 commits past that sha", on_branch == "2", "count=" + on_branch)

print()
print("=== 1. entry counts, from the manifest BLOBS themselves ===")
old = parse_manifest(git("show", FORK + ":" + MANIFEST))
new = parse_manifest(open(ROOT + "/" + MANIFEST, "rb").read())
check("manifest at the fork sha holds 430 entries", len(old) == 430, "len=%d" % len(old))
check("manifest on disk today holds 571 entries", len(new) == 571, "len=%d" % len(new))
check("571 - 430 = 141 added", len(new) - len(old) == 141, "delta=%d" % (len(new) - len(old)))

print()
print("=== 2. nothing pre-existing was DROPPED or RENAMED ===")
dropped = sorted(set(old) - set(new))
check("0 pre-existing entries dropped", not dropped, "dropped: %s" % dropped[:10])

print()
print("=== 3. RECOMPUTED: every pre-existing file's bytes today == its bytes at the fork sha ===")
print("      (recomputed from the git blob and from disk; the manifest's recorded hash is")
print("       used only as a THIRD cross-check, never as the source of truth)")
identical = manifest_agrees = 0
byte_diff = []
manifest_disagree = []
missing_on_disk = []
unreadable = []
for name in sorted(old):
    rel = CAPREL + "/" + name
    try:
        at_fork = git("show", FORK + ":" + rel)
    except subprocess.CalledProcessError as exc:
        unreadable.append((name, "not in the fork-point tree: %r" % exc))
        continue
    try:
        with open(ROOT + "/" + rel, "rb") as fh:
            today = fh.read()
    except OSError as exc:                       # NAMED, not swallowed (P-40)
        missing_on_disk.append((name, repr(exc)))
        continue
    h_fork = hashlib.sha256(at_fork).hexdigest()
    h_today = hashlib.sha256(today).hexdigest()
    if h_fork == h_today:
        identical += 1
    else:
        byte_diff.append((name, h_fork, h_today))
    if new.get(name) == h_today:
        manifest_agrees += 1
    else:
        manifest_disagree.append((name, new.get(name), h_today))

print("      enumerated %d pre-existing entries" % len(old))
print("      byte-identical fork-vs-today       : %d" % identical)
print("      DIFFER                             : %d" % len(byte_diff))
print("      missing on disk (named, not skipped): %d %s" % (len(missing_on_disk), missing_on_disk[:5]))
print("      not in the fork tree (named)        : %d %s" % (len(unreadable), unreadable[:5]))
print("      current manifest hash agrees w/ disk: %d" % manifest_agrees)
for n, a, b in byte_diff[:20]:
    print("        DIFF %s\n             fork  %s\n             today %s" % (n, a, b))
for n, a, b in manifest_disagree[:20]:
    print("        MANIFEST MISMATCH %s\n             manifest %s\n             disk     %s" % (n, a, b))

check("all 430 pre-existing files are byte-identical to the fork sha",
      identical == 430 and not byte_diff and not missing_on_disk and not unreadable,
      "identical=%d differ=%d missing=%d unreadable=%d" % (identical, len(byte_diff),
                                                          len(missing_on_disk), len(unreadable)))
check("and the CURRENT manifest records those same recomputed hashes (no laundering)",
      manifest_agrees == 430, "agrees=%d" % manifest_agrees)

print()
print("=== 4. the git diff agrees: exactly one pre-existing path modified ===")
ns = git("diff", "--name-status", FORK + "..." + A2_7_HEAD).decode().split("\n")
mods = [l for l in ns if l and not l.startswith("A\t")]
check("the ONLY non-Added path in the whole branch is MANIFEST.sha256",
      mods == ["M\t" + MANIFEST], "non-added: %s" % mods)

print()
print("FAILURES: %d" % len(fails))
for f in fails:
    print("  - " + f)
sys.exit(1 if fails else 0)
