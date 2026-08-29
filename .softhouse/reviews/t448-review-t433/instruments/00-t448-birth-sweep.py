#!/usr/bin/env python3
"""
T448 -- INDEPENDENT RE-DERIVATION of T433's whole-632 birth-blob sweep.

WHY THIS EXISTS.  T433 claims 632 post-fork observations, 632 born strictly older than the
tip and ancestors of it, 631 byte-equal to their birth blob and exactly 1 different. Those
are the AUTHOR'S numbers. A reviewer that re-runs the author's own instrument has measured
the instrument, not the world, so this file does not import, call, or copy
`00-t433-whole-632-birth-sweep.py`.

ENGINE (P-33/P-53): git plumbing only -- `git ls-tree`, `git rev-list`, `git rev-parse`,
`git cat-file`, `git merge-base --is-ancestor`, and Python `hashlib`. NO regular expression
is used to derive any number here, so there is no regex dialect to get wrong.

THE INDEPENDENT DERIVATION OF "BIRTH", stated so the difference is checkable.
  T433 METHOD A : per path, `git log --diff-filter=A --format=%H -- <path>`, last line.
  T433 METHOD B : one bulk `git log --diff-filter=A --name-only` walked newest-first.
  Both are the SAME primitive (`--diff-filter=A`, which is rename-aware and therefore
  reports a high-similarity rename as R and not A) read two ways. Agreement between them
  is weaker evidence than it looks.
  T448 METHOD C : TREE CONTAINMENT. Walk `git rev-list --reverse --topo-order <TIP>` and,
  for each commit in that order, ask whether the path is present in that commit's tree.
  The FIRST commit in a topological order whose tree contains the path is a commit all of
  whose ancestors lack it -- i.e. the birth commit -- and it is an ancestor of TIP by
  construction. `--diff-filter` is never used. Rename detection cannot affect it, because
  containment is a property of a tree and not of a diff.
  Cost control: consecutive commits usually share the same subtree OID, so the subtree OID
  is resolved per commit (one cheap `rev-parse`) and `ls-tree` runs only when it CHANGES.

CALIBRATION BEFORE ANY NEGATIVE (P-72; C4).  Two known positives are asserted findable
before this file is allowed to report a single "equal" count:
  K1  the fork sha resolves and contains a non-empty observation set (else the population
      is meaningless and every path would look post-fork);
  K2  METHOD C reproduces a birth commit for a path whose birth is INDEPENDENTLY known --
      a fork-era path must come out born at an ancestor of the fork sha.
A run in which either calibration fails REFUSES with exit 2 and prints no counts.

CORPUS ASSERTION (C3).  An empty population, an unresolved birth, or a non-blob entry is
exit 2, never exit 0. A zero-difference table over an empty population is the exact vacuous
pass this whole review chain exists to refuse.

EXIT: 0 = the sweep completed and its findings are printed; 2 = REFUSED, no verdict.
"""
import hashlib
import os
import subprocess
import sys

FORK = "12a7f8d9a3af4665fd5281a9f9c001d4f1276a53"   # literal fork sha, never merge-base (P-24)
CAPREL = ".softhouse/capture/tierA-a2"
SUBDIRS = ("out", "req")


def refuse(*lines):
    print()
    for ln in lines:
        print("REFUSED: %s" % ln)
    sys.exit(2)


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=True).stdout


def git_ok(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode == 0


try:
    ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=True).stdout.decode().strip()
except (subprocess.CalledProcessError, OSError) as exc:
    print("REFUSED: this is not a git worktree: %r" % exc)
    sys.exit(2)

TIP = sys.argv[1] if len(sys.argv) > 1 else "HEAD"

print("=== T448 INDEPENDENT BIRTH SWEEP (METHOD C: tree containment, topo order) ===")
print("    root          %s" % ROOT)
try:
    tip_sha = git("rev-parse", TIP).decode().strip()
except subprocess.CalledProcessError as exc:
    refuse("TIP %r does not resolve: %r" % (TIP, exc))
print("    tip           %s  (%s)" % (tip_sha, TIP))
print("    fork constant %s" % FORK)

if not git_ok("cat-file", "-e", FORK + "^{commit}"):
    refuse("the fork sha %s is not a commit in this repository." % FORK,
           "K1 CALIBRATION FAILED. Without it every path looks post-fork and the population",
           "count below would be a fabrication.")


def obs_at(rev):
    """path -> (mode, type, oid) for every entry under CAPREL/{out,req} in rev's tree."""
    out = {}
    for sub in SUBDIRS:
        try:
            raw = git("ls-tree", "-r", "-z", rev, "--", "%s/%s" % (CAPREL, sub))
        except subprocess.CalledProcessError:
            raw = b""
        for rec in raw.split(b"\x00"):
            if not rec:
                continue
            meta, _, path = rec.partition(b"\t")
            mode, otype, oid = meta.decode().split()
            out[path.decode()] = (mode, otype, oid)
    return out


head_obs = obs_at(tip_sha)
fork_obs = obs_at(FORK)
if not fork_obs:
    refuse("K1 CALIBRATION FAILED: the fork sha contains ZERO observations under %s." % CAPREL,
           "A sweep whose baseline commit is empty reports every path as post-fork.")
print("    K1 calibration OK: the fork tree carries %d observation(s)." % len(fork_obs))

post = sorted(set(head_obs) - set(fork_obs))
print()
print("--- (0) POPULATION -----------------------------------------------------------")
print("    at tip   %d      at fork   %d      POST-FORK POPULATION  %d"
      % (len(head_obs), len(fork_obs), len(post)))
if not post:
    refuse("the post-fork population is EMPTY. Either the selector broke or the fork",
           "constant moved onto the tip. No count below would mean anything.")
nonblob = sorted(p for p in post if head_obs[p][1] != "blob")
if nonblob:
    refuse("%d post-fork entries are not blobs (symlink/gitlink): %s"
           % (len(nonblob), nonblob[:5]))
print("    non-blob (symlink/gitlink) entries in the population : 0")

# ---------------------------------------------------------------------------
# METHOD C -- first commit, in topological order from the root, whose tree contains the path.
# ---------------------------------------------------------------------------
commits = git("rev-list", "--reverse", "--topo-order", tip_sha).decode().split()
print()
print("--- (1) METHOD C: tree containment over %d commits, oldest-first ----------------"
      % len(commits))
birth = {}
wanted = set(post)
prev_key, prev_present = None, {}
scanned = 0
for c in commits:
    key = []
    for sub in SUBDIRS:
        r = subprocess.run(["git", "rev-parse", "--verify", "-q",
                            "%s:%s/%s" % (c, CAPREL, sub)], cwd=ROOT,
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        key.append(r.stdout.decode().strip())
    key = tuple(key)
    if key == prev_key:
        present = prev_present
    else:
        present = {}
        for sub, tsha in zip(SUBDIRS, key):
            if not tsha:
                continue
            raw = git("ls-tree", "-r", "-z", "--name-only", c, "--", "%s/%s" % (CAPREL, sub))
            for rec in raw.split(b"\x00"):
                if rec:
                    present[rec.decode()] = True
        scanned += 1
        prev_key, prev_present = key, present
    if not wanted:
        continue
    born_here = [p for p in wanted if p in present]
    for p in born_here:
        birth[p] = c
        wanted.discard(p)
print("    distinct subtree states listed : %d" % scanned)
print("    birth commit resolved for      : %d of %d" % (len(birth), len(post)))
if wanted:
    refuse("%d post-fork path(s) have NO birth commit under METHOD C: %s"
           % (len(wanted), sorted(wanted)[:5]),
           "A path present at the tip that is in no ancestor tree is impossible; this is an",
           "instrument failure and must not be reported as a clean sweep.")

# K2 CALIBRATION: a path that existed AT THE FORK must come out born at an ancestor of the fork.
cal_path = sorted(fork_obs)[0]
cal_birth = None
for c in commits:
    if git_ok("cat-file", "-e", "%s:%s" % (c, cal_path)):
        cal_birth = c
        break
if cal_birth is None:
    refuse("K2 CALIBRATION FAILED: no commit in the tip's history contains the known fork-era",
           "path %s. METHOD C cannot find a birth it is guaranteed to find." % cal_path)
if not git_ok("merge-base", "--is-ancestor", cal_birth, FORK):
    refuse("K2 CALIBRATION FAILED: %s came out born at %s, which is NOT an ancestor of the"
           % (cal_path, cal_birth), "fork sha, though the path demonstrably exists in the fork tree.")
print("    K2 calibration OK: fork-era path %s" % cal_path[len(CAPREL) + 1:])
print("       born at %s, an ancestor of the fork sha, as it must be." % cal_birth[:12])

# ---------------------------------------------------------------------------
# (2) WHERE each was born, relative to the tip.
# ---------------------------------------------------------------------------
older_anc, at_tip, not_anc = 0, [], []
for p in post:
    b = birth[p]
    if b == tip_sha:
        at_tip.append(p)
    elif git_ok("merge-base", "--is-ancestor", b, tip_sha):
        older_anc += 1
    else:
        not_anc.append((p, b))
print()
print("--- (2) WHERE EACH OBSERVATION WAS BORN ----------------------------------------")
print("    born STRICTLY OLDER than the tip and an ANCESTOR of it : %d" % older_anc)
print("    born AT THE TIP itself                                 : %d" % len(at_tip))
print("    born at a commit that is NOT an ancestor of the tip    : %d" % len(not_anc))
for p in at_tip[:10]:
    print("      BORN-AT-TIP %s" % p[len(CAPREL) + 1:])
for p, b in not_anc[:10]:
    print("      NOT-ANCESTOR %s born at %s" % (p[len(CAPREL) + 1:], b))
print("    distinct birth commits : %d" % len(set(birth.values())))

# ---------------------------------------------------------------------------
# (3) OID comparison, then (4) sha256 of bytes. Two comparisons, one reads no bytes.
# ---------------------------------------------------------------------------
oid_diff, sha_diff, sha_same, oid_same = [], [], 0, 0
for p in post:
    b = birth[p]
    birth_oid = git("rev-parse", "%s:%s" % (b, p)).decode().strip()
    if birth_oid == head_obs[p][2]:
        oid_same += 1
    else:
        oid_diff.append((p, b, birth_oid, head_obs[p][2]))
    birth_bytes = git("cat-file", "blob", birth_oid)
    disk = os.path.join(ROOT, p)
    try:
        with open(disk, "rb") as fh:
            disk_bytes = fh.read()
    except OSError as exc:
        refuse("%s is tracked at the tip but unreadable on disk: %r" % (p, exc))
    h0 = hashlib.sha256(birth_bytes).hexdigest()
    h1 = hashlib.sha256(disk_bytes).hexdigest()
    if h0 == h1:
        sha_same += 1
    else:
        sha_diff.append((p, b, h0, h1))

print()
print("--- (3) GIT BLOB OID: birth tree vs tip tree (no bytes read) --------------------")
print("    equal to the birth blob : %d" % oid_same)
print("    DIFFER                  : %d" % len(oid_diff))
for p, b, o0, o1 in oid_diff:
    print("      DIFFERS %s" % p[len(CAPREL) + 1:])
    print("        born at   %s" % b)
    print("        birth oid %s" % o0)
    print("        tip   oid %s" % o1)
print()
print("--- (4) SHA256: bytes at birth vs bytes on disk ---------------------------------")
print("    equal to the birth blob : %d" % sha_same)
print("    DIFFER                  : %d" % len(sha_diff))
for p, b, h0, h1 in sha_diff:
    print("      DIFFERS %s" % p[len(CAPREL) + 1:])
    print("        born at      %s" % b)
    print("        birth sha256 %s" % h0)
    print("        disk  sha256 %s" % h1)

# ---------------------------------------------------------------------------
# (5) CROSS-CHECK against T433's primitive, run here only to compare, never to derive.
# ---------------------------------------------------------------------------
print()
print("--- (5) CROSS-CHECK against T433's PRIMITIVE, which METHOD C did not use ---------")
print("    `git log --diff-filter=A` is run here ONLY to see whether it AGREES with METHOD C.")
print("    A disagreement is a finding about T433's instrument, not about the repository.")
a_resolved, disagree = 0, []
for p in post:
    try:
        lines = git("log", tip_sha, "--diff-filter=A", "--format=%H", "--", p).decode().split()
    except subprocess.CalledProcessError:
        lines = []
    a = lines[-1] if lines else None
    if a is not None:
        a_resolved += 1
    if a != birth[p]:
        disagree.append((p, a, birth[p]))
print("    METHOD A resolved    : %d of %d" % (a_resolved, len(post)))
print("    A vs C disagreements : %d" % len(disagree))
for p, a, c in disagree[:10]:
    print("      DISAGREE %s  A=%s  C=%s" % (p[len(CAPREL) + 1:], a, c))

print()
print("CONCLUSION")
print("  A committed baseline strictly older than the tip exists for %d of the %d post-fork"
      % (older_anc, len(post)))
print("  observations. Non-equal by sha256, by name: %s"
      % [p[len(CAPREL) + 1:] for p, _, _, _ in sha_diff])
sys.exit(0)
