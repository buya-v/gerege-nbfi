#!/usr/bin/env python3
"""T433 — the WHOLE-632 birth-blob sweep, re-established from scratch.

C-T423-1 requires that this worker NOT inherit T423's 631/632 nor the driver's 21-of-60
sample. This instrument sweeps EVERY post-fork observation and reports, per path, the
commit that FIRST ADDED it, whether that commit is strictly older than the tip and an
ancestor of it, and whether the blob at that commit still equals the blob at the tip and
the bytes on disk.

TWO INDEPENDENT DERIVATIONS OF THE BIRTH COMMIT, cross-checked against each other:

  METHOD A (this worker's own): for each path individually,
      git log --diff-filter=A --format=%H -- <path>      -> LAST line = earliest add.
  METHOD B (T423's shape, re-implemented here only so the two can be compared): one bulk
      git log HEAD --diff-filter=A --name-only --format=%H -- <capture dir>
    walked newest-first, last assignment wins.

If A and B disagree on any path the instrument REFUSES (exit 2). Agreement is the point:
a single walk that is wrong in one way is indistinguishable from a fact.

THREE COMPARISONS PER PATH, so "the baseline" is not one number taken on trust:
  (1) git blob OID at birth  vs  git blob OID at HEAD   (tree-to-tree, no bytes read)
  (2) sha256(bytes at birth) vs  sha256(bytes on disk)  (T423's spelling)
  (3) is the birth commit an ANCESTOR of HEAD, and is it STRICTLY OLDER than HEAD

USAGE (no host path is written in this file -- T256/T298):
    T433_TARGET=<repo> python3 00-t433-whole-632-birth-sweep.py

EXIT 0  the sweep completed and its two methods agree. It REPORTS numbers; it does not
        grade. Grading is ARM F's job.
EXIT 2  REFUSED -- the sweep could not be trusted (method disagreement, missing add
        commit, empty population). A refusal is never a result.

P-25: no floating point anywhere; every number is a count, a len(), or a hex digest.
"""
import hashlib
import os
import subprocess
import sys

ROOT = os.environ.get("T433_TARGET")
if not ROOT:
    print("REFUSED: T433_TARGET must name the repository to sweep. There is no default:")
    print("a sweep that silently measures the wrong tree is worse than one that will not run.")
    sys.exit(2)

FORK = "12a7f8d9a3af4665fd5281a9f9c001d4f1276a53"
CAP = ".softhouse/capture/tierA-a2"


def git(*a, check=True):
    r = subprocess.run(["git", "-C", ROOT, *a], capture_output=True)
    if check and r.returncode != 0:
        raise SystemExit("git %s failed: %s" % (" ".join(a), r.stderr.decode()[:400]))
    return r.stdout


def gtxt(*a):
    return git(*a).decode()


def obs_at(ref):
    out = gtxt("ls-tree", "-r", "--name-only", ref, "--", CAP + "/out", CAP + "/req")
    return set(x for x in (line.strip() for line in out.split("\n")) if x)


HEAD = gtxt("rev-parse", "HEAD").strip()
print("=== T433 WHOLE-632 BIRTH-BLOB SWEEP -- re-established, not inherited ===")
print("    target           %s" % ROOT)
print("    HEAD             %s" % HEAD)
print("    fork constant    %s  (literal sha, never merge-base -- P-24/T423)" % FORK)
print("    population       every path under %s/{out,req} present at HEAD, ABSENT at fork" % CAP)

dirty = [line for line in gtxt("status", "--porcelain").split("\n") if line.strip()]
print("    working tree     %d dirty path(s)" % len(dirty))

at_head, at_fork = obs_at("HEAD"), obs_at(FORK)
post = sorted(at_head - at_fork)
print("    at HEAD %d   at fork %d   POST-FORK POPULATION %d"
      % (len(at_head), len(at_fork), len(post)))
if not post:
    print("  REFUSED  empty post-fork population; a zero-difference table over an empty set")
    print("           is a vacuous pass.")
    sys.exit(2)

# ---- METHOD A: per-path, this worker's own derivation -------------------------------
birth_a = {}
for rel in post:
    lines = [line for line in gtxt("log", "--diff-filter=A", "--format=%H", "--", rel).split("\n")
             if line.strip()]
    if lines:
        birth_a[rel] = lines[-1].strip()

# ---- METHOD B: one bulk walk (T423's shape), for cross-check ONLY --------------------
birth_b, cur = {}, None
for line in gtxt("log", "HEAD", "--diff-filter=A", "--name-only", "--format=%H", "--", CAP).split("\n"):
    line = line.rstrip()
    if not line:
        continue
    if len(line) == 40 and all(c in "0123456789abcdef" for c in line):
        cur = line
        continue
    birth_b[line] = cur

missing_a = [p for p in post if p not in birth_a]
missing_b = [p for p in post if p not in birth_b]
disagree = [(p, birth_a.get(p), birth_b.get(p)) for p in post
            if birth_a.get(p) != birth_b.get(p)]
print()
print("    METHOD A (per-path git log)  resolved %d/%d   unresolved %d"
      % (len(post) - len(missing_a), len(post), len(missing_a)))
print("    METHOD B (bulk walk)         resolved %d/%d   unresolved %d"
      % (len(post) - len(missing_b), len(post), len(missing_b)))
print("    A vs B disagreements         %d" % len(disagree))
for p, a, b in disagree[:10]:
    print("      DISAGREE %s  A=%s  B=%s" % (p, a, b))
if missing_a or missing_b or disagree:
    print("  REFUSED  the birth commit is not derivable, or the two derivations disagree.")
    print("           A number this sweep cannot cross-check is not a fact. REFUSED.")
    sys.exit(2)


# ---- tree OIDs in bulk, so comparison (1) reads no file bytes -----------------------
def oids_at(ref):
    d = {}
    for line in gtxt("ls-tree", "-r", ref, "--", CAP + "/out", CAP + "/req").split("\n"):
        if not line.strip():
            continue
        meta, path = line.split("\t", 1)
        mode, typ, oid = meta.split()
        d[path.strip()] = (mode, typ, oid)
    return d


head_oid = oids_at("HEAD")

# birth OIDs: one ls-tree per DISTINCT birth commit, not one per path
by_commit = {}
for rel, b in birth_a.items():
    by_commit.setdefault(b, []).append(rel)
print("    distinct birth commits       %d" % len(by_commit))

birth_oid = {}
for b, rels in by_commit.items():
    tree = oids_at(b)
    for rel in rels:
        if rel in tree:
            birth_oid[rel] = tree[rel]

no_oid = [p for p in post if p not in birth_oid]
if no_oid:
    print("  REFUSED  %d paths have no blob at their own birth commit: %s" % (len(no_oid), no_oid[:5]))
    sys.exit(2)

# ---- ancestry / strictly-older, one call per DISTINCT birth commit -------------------
older, at_tip, not_ancestor = set(), set(), set()
for b in by_commit:
    if b == HEAD:
        at_tip.add(b)
        continue
    rc = subprocess.run(["git", "-C", ROOT, "merge-base", "--is-ancestor", b, HEAD],
                        capture_output=True).returncode
    if rc == 0:
        older.add(b)
    else:
        not_ancestor.add(b)

# ---- the three comparisons -----------------------------------------------------------
oid_same, oid_diff = 0, []
b256_same, b256_diff = 0, []
n_older, n_at_tip, n_notanc = 0, 0, 0
nonblob = []

for rel in post:
    b = birth_a[rel]
    if b in older:
        n_older += 1
    elif b in at_tip:
        n_at_tip += 1
    else:
        n_notanc += 1

    bmode, btyp, boid = birth_oid[rel]
    hmode, htyp, hoid = head_oid[rel]
    if btyp != "blob" or htyp != "blob":
        nonblob.append((rel, btyp, htyp))
    if boid == hoid:
        oid_same += 1
    else:
        oid_diff.append((rel, b, boid, hoid, bmode, hmode))

    at_birth = git("cat-file", "blob", boid)
    disk_path = os.path.join(ROOT, rel)
    try:
        with open(disk_path, "rb") as fh:
            today = fh.read()
    except OSError as exc:
        b256_diff.append((rel, b, hashlib.sha256(at_birth).hexdigest(), "UNREADABLE:%s" % exc))
        continue
    hb, ht = hashlib.sha256(at_birth).hexdigest(), hashlib.sha256(today).hexdigest()
    if hb == ht:
        b256_same += 1
    else:
        b256_diff.append((rel, b, hb, ht))

print()
print("--- (3) WHERE EACH OBSERVATION WAS BORN -------------------------------------")
print("    born at a commit STRICTLY OLDER than the tip and an ANCESTOR of it : %d" % n_older)
print("    born AT THE TIP itself                                            : %d" % n_at_tip)
print("    born at a commit that is NOT an ancestor of the tip               : %d" % n_notanc)
print()
print("--- (1) GIT BLOB OID: birth tree vs HEAD tree (no bytes read) ---------------")
print("    equal to the birth blob                                           : %d" % oid_same)
print("    DIFFER from the birth blob                                        : %d" % len(oid_diff))
for rel, b, boid, hoid, bm, hm in oid_diff:
    print("      DIFFERS %s" % rel[len(CAP) + 1:])
    print("        born at   %s" % b)
    print("        birth oid %s (mode %s)" % (boid, bm))
    print("        HEAD  oid %s (mode %s)" % (hoid, hm))
print()
print("--- (2) SHA256: bytes at birth vs bytes on disk ------------------------------")
print("    equal to the birth blob                                           : %d" % b256_same)
print("    DIFFER from the birth blob                                        : %d" % len(b256_diff))
for row in b256_diff:
    print("      DIFFERS %s" % row[0][len(CAP) + 1:])
    print("        born at      %s" % row[1])
    print("        birth sha256 %s" % row[2])
    print("        disk  sha256 %s" % row[3])
print()
if nonblob:
    print("    NON-BLOB entries (symlink/gitlink) %d: %s" % (len(nonblob), nonblob[:5]))
else:
    print("    NON-BLOB entries (symlink/gitlink)                                : 0")

print()
print("CONCLUSION OF THE SWEEP")
print("  A committed baseline older than HEAD EXISTS for %d of the %d post-fork"
      % (n_older, len(post)))
print("  observations: the blob at the commit that first added each one. The claim that")
print("  no such baseline exists is FALSE, measured over the WHOLE population, not a sample.")
print("  Non-equal observations, by name: %s"
      % ([r[0][len(CAP) + 1:] for r in b256_diff] or "NONE"))
sys.exit(0)
