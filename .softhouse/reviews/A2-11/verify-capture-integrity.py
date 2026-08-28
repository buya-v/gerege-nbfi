#!/usr/bin/env python3
"""T374 (T362 F-1) — EVIDENCE INTEGRITY for the tierA-a2 captured oracle observations,
with its OWN exit code, adjudicated GREEN, so run-all.sh's aggregate verdict can see it.

WHY THIS FILE EXISTS — the measurement, not the theory.

run-all.sh section 4 (verify-manifest-independently.py) does check the byte-identity of the
pre-existing capture corpus, and its third arm prints any mutated file BY NAME. But section 4
is adjudicated RC 1, because its first two arms pin manifest COUNTS taken at A2-7's moment
and the rig has grown since. A section that is already failing is SATURATED: the integrity
arm cannot make it any redder, so the aggregate verdict cannot distinguish "section 4 is red
for drift, as adjudicated" from "section 4 is red for drift AND a captured oracle observation
was mutated". T362 proved this by appending a marker to a real captured observation,
.../out/A2-000-glaccounts-preexisting.http:

    verify-manifest-independently.py  rc=1   DIFF out/A2-000-glaccounts-preexisting.http
    run-all.sh                        rc=0   4  EXPECTED 1  ACTUAL 1  "as adjudicated"
                                             deviations: 0   RUN-ALL VERDICT: PASS

T374 reproduced that exactly, in a scratch clone, before writing this file (P-22 — every fix
driven RED first). Evidence: .softhouse/capture/t374-t362-conditions/out/.

THAT IS AN EVIDENCE-INTEGRITY DEFECT, NOT A COSMETIC ONE. The captured observations under
out/ and req/ ARE the record this program grades against. An exit status that stays 0 while
one of them is mutated means the corpus can rot with the harness saying PASS. It is the same
defect class T357 removed one level up: a status that cannot get worse carries no information.

>>> DO NOT READ run-all.sh's EXIT 0 AS "THE EVIDENCE IS INTACT" ON ANY VERSION THAT PREDATES
>>> THIS FILE. Before T374 it was not sensitive to a mutated capture. From T374 it is, because
>>> the integrity question is asked HERE, where GREEN is the adjudicated value and any
>>> deviation therefore moves the section and fails the aggregate.

WHAT THIS FILE DOES AND DOES NOT COVER (P-40 — the boundary is stated, not implied):
  * COVERS   every file under .softhouse/capture/tierA-a2/{out,req}/ — the captured oracle
             observations and the request bodies that produced them — in two independent
             directions: against the LITERAL fork sha (the historical baseline section 4
             uses) and against HEAD (which also covers observations captured since).
  * DOES NOT COVER  other capture directories, .softhouse/vectors/, or obs/ under this
             review. obs/ byte-identity is graded at the git-object level by the reviewer,
             and the graded vector store is graded by conformance.sh. Named so that silence
             here is distinguishable from not looking.

P-25: no floating point. The only numbers are counts from len() and sha256 hex digests.
P-24: the historical baseline is a LITERAL immutable sha, never `git merge-base`.
P-22: the comparator is driven RED against mutated bytes in memory before it is trusted, and
      end-to-end against a mutated file in a scratch copy by
      .softhouse/capture/t374-t362-conditions/prove-t374-fixes-can-fail.sh.

EXIT CODES
  0  every captured observation is byte-identical in both directions.
  1  at least one captured observation DIFFERS or is MISSING. Named, never counted only.
  2  REFUSED — the instrument could not measure (empty population, unusable git, missing
     baseline). A refusal is never reported as a pass.
"""
import hashlib
import os
import pathlib
import subprocess
import sys

# Root derivation matches the other A2-11 scripts: this file sits three levels below the
# checkout root, under reviews/A2-11, so parents[3] IS that root. A2_11_ROOT overrides.
ROOT = os.environ.get("A2_11_ROOT") or str(pathlib.Path(__file__).resolve().parents[3])
CAPREL = ".softhouse/capture/tierA-a2"
OBS_DIRS = ("out", "req")
# LITERAL, immutable (P-24). A2-7's fork point; the same baseline section 4 uses.
FORK = "12a7f8d9a3af4665fd5281a9f9c001d4f1276a53"

fails = []
refusals = []


def check(label, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + label + (("\n          " + detail) if detail else ""))
    if not cond:
        fails.append(label)


def refuse(*lines):
    for i, line in enumerate(lines):
        print(("  REFUSED  " if i == 0 else "           ") + line)
    refusals.append(lines[0])


def git(*args, check_rc=True):
    return subprocess.run(["git", "-C", ROOT, *args], capture_output=True,
                          check=check_rc).stdout


def sha(b):
    return hashlib.sha256(b).hexdigest()


print("=== 0. THE INSTRUMENT ITSELF — driven RED before it is trusted (P-22) ===")
_a = b"HTTP/1.1 200 OK\r\n\r\n{\"id\":2}\n"
_b = _a + b"\nT374-SELFTEST-MARKER\n"
check("the comparator reports IDENTICAL on identical bytes", sha(_a) == sha(_a), sha(_a)[:16])
check("the comparator reports DIFFERENT on bytes with ONE line appended — the exact "
      "mutation shape T362 used to prove F-1", sha(_a) != sha(_b),
      "%s vs %s" % (sha(_a)[:16], sha(_b)[:16]))

print()
print("=== 1. THE BASELINE EXISTS — a missing baseline is REFUSED, never read as clean ===")
have_fork = subprocess.run(["git", "-C", ROOT, "cat-file", "-e", FORK + "^{commit}"],
                           capture_output=True).returncode == 0
if not have_fork:
    refuse("the literal fork sha %s is not present in this repository." % FORK[:12],
           "That is an INSTRUMENT failure, not a clean corpus. With no baseline there is",
           "nothing to compare the captured observations against, and a comparison that",
           "cannot run is not a comparison that passed.")
else:
    print("  PASS  literal baseline sha %s is present" % FORK[:12])

print()
print("=== 2. POPULATION — enumerated from the fork tree AND from HEAD ===")
print("    An EMPTY population is a SELECTOR failure, not a clean tree: this repository")
print("    tracks captured oracle observations under %s/{out,req}/ and always" % CAPREL)
print("    has. An empty census passes everything. REFUSED. (Same spelling as")
print("    guard_guards_dir_registration in conformance.sh — one idea, one spelling.)")

fork_paths = []
if have_fork:
    for line in git("ls-tree", "-r", "--name-only", FORK, "--", CAPREL).decode().split("\n"):
        line = line.strip()
        if not line:
            continue
        rest = line[len(CAPREL) + 1:] if line.startswith(CAPREL + "/") else ""
        if rest.split("/")[0] in OBS_DIRS:
            fork_paths.append(line)
fork_paths.sort()

head_paths = sorted(
    line.strip()
    for line in git("ls-tree", "-r", "--name-only", "HEAD", "--", CAPREL).decode().split("\n")
    if line.strip()
    and line.strip().startswith(CAPREL + "/")
    and line.strip()[len(CAPREL) + 1:].split("/")[0] in OBS_DIRS)

per_dir_fork = {d: len([p for p in fork_paths if p.startswith(CAPREL + "/" + d + "/")])
                for d in OBS_DIRS}
per_dir_head = {d: len([p for p in head_paths if p.startswith(CAPREL + "/" + d + "/")])
                for d in OBS_DIRS}
print("      at the fork sha : %d observations  %s" % (len(fork_paths), per_dir_fork))
print("      at HEAD         : %d observations  %s" % (len(head_paths), per_dir_head))

if have_fork and (not fork_paths or any(v == 0 for v in per_dir_fork.values())):
    refuse("the fork-sha observation population is EMPTY or missing a whole directory: %s"
           % per_dir_fork,
           "SELECTOR failure. A zero-difference table over an empty population is a",
           "vacuous pass. REFUSED.")
if not head_paths or any(v == 0 for v in per_dir_head.values()):
    refuse("the HEAD observation population is EMPTY or missing a whole directory: %s"
           % per_dir_head,
           "SELECTOR failure. REFUSED.")

print()
print("=== 3. ARM A — every observation that existed at the fork sha, RECOMPUTED ===")
print("    git blob at %s  vs  the bytes on disk today." % FORK[:12])
a_identical = 0
a_diff = []
a_missing = []
a_unreadable = []
for rel in fork_paths:
    try:
        at_fork = git("show", FORK + ":" + rel)
    except subprocess.CalledProcessError as exc:      # NAMED, never swallowed (P-40)
        a_unreadable.append((rel, repr(exc)))
        continue
    try:
        with open(os.path.join(ROOT, rel), "rb") as fh:
            today = fh.read()
    except OSError as exc:
        a_missing.append((rel, repr(exc)))
        continue
    if sha(at_fork) == sha(today):
        a_identical += 1
    else:
        a_diff.append((rel, sha(at_fork), sha(today)))

print("      enumerated                : %d" % len(fork_paths))
print("      byte-identical            : %d" % a_identical)
print("      DIFFER                    : %d" % len(a_diff))
print("      MISSING on disk           : %d" % len(a_missing))
print("      unreadable at the fork sha: %d" % len(a_unreadable))
for rel, h0, h1 in a_diff:
    print("        MUTATED %s\n                fork  %s\n                today %s" % (rel, h0, h1))
for rel, exc in a_missing:
    print("        MISSING %s  %s" % (rel, exc))
for rel, exc in a_unreadable:
    print("        UNREADABLE %s  %s" % (rel, exc))

check("NO captured oracle observation that existed at the fork sha has been MUTATED",
      not a_diff, "differ=%d" % len(a_diff))
check("NO captured oracle observation that existed at the fork sha has been DELETED",
      not a_missing and not a_unreadable,
      "missing=%d unreadable=%d" % (len(a_missing), len(a_unreadable)))

print()
print("=== 4. ARM B — every observation tracked at HEAD, including ones captured SINCE ===")
print("    git blob at HEAD  vs  the bytes on disk. Arm A cannot see an observation that")
print("    did not exist at the fork sha; %d of the %d tracked today are in that class."
      % (len(head_paths) - len(fork_paths), len(head_paths)))
b_identical = 0
b_diff = []
b_missing = []
for rel in head_paths:
    at_head = git("show", "HEAD:" + rel)
    try:
        with open(os.path.join(ROOT, rel), "rb") as fh:
            today = fh.read()
    except OSError as exc:
        b_missing.append((rel, repr(exc)))
        continue
    if sha(at_head) == sha(today):
        b_identical += 1
    else:
        b_diff.append((rel, sha(at_head), sha(today)))

print("      enumerated     : %d" % len(head_paths))
print("      byte-identical : %d" % b_identical)
print("      DIFFER         : %d" % len(b_diff))
print("      MISSING on disk: %d" % len(b_missing))
for rel, h0, h1 in b_diff:
    print("        MUTATED %s\n                HEAD  %s\n                disk  %s" % (rel, h0, h1))
for rel, exc in b_missing:
    print("        MISSING %s  %s" % (rel, exc))

check("NO captured oracle observation tracked at HEAD differs from its committed bytes",
      not b_diff, "differ=%d" % len(b_diff))
check("NO captured oracle observation tracked at HEAD is missing from the working tree",
      not b_missing, "missing=%d" % len(b_missing))

print()
print("=== 5. POSITIVE CONTROL — the two arms actually READ bytes ===")
check("ARM A compared a non-empty population", have_fork and len(fork_paths) > 0,
      "%d observations at the fork sha" % len(fork_paths))
check("ARM B compared a non-empty population", len(head_paths) > 0,
      "%d observations at HEAD" % len(head_paths))
check("ARM B's population is a SUPERSET of ARM A's — every historical observation is still "
      "tracked, so neither arm is silently narrower than it reads",
      set(fork_paths) <= set(head_paths),
      "in fork but not at HEAD: %s" % sorted(set(fork_paths) - set(head_paths))[:10])

print()
if refusals:
    print("REFUSALS: %d" % len(refusals))
    for r in refusals:
        print("  - " + r)
print("FAILURES: %d" % len(fails))
for f in fails:
    print("  - " + f)

if refusals:
    print()
    print("VERDICT: REFUSED (exit 2). The instrument could not measure. This is NOT a pass,")
    print("and run-all.sh adjudicates this section to 0, so a refusal moves it and fails the")
    print("aggregate verdict.")
    sys.exit(2)
if fails:
    print()
    print("VERDICT: FAIL (exit 1). A CAPTURED ORACLE OBSERVATION HAS BEEN MUTATED OR LOST.")
    print("This is the evidence the whole program grades against. Do not repair it by")
    print("re-capturing and committing over the top: that launders the mutation into the")
    print("record. Establish what changed, and why, first.")
    sys.exit(1)
print()
print("VERDICT: PASS (exit 0). Every captured oracle observation under %s/{out,req}/"
      % CAPREL)
print("is byte-identical to both its fork-sha blob and its HEAD blob.")
sys.exit(0)
