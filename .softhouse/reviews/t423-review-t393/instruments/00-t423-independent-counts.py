#!/usr/bin/env python3
"""T423 — INDEPENDENT re-derivation of the 403 / 1035 / 632 number set that every other
claim in T393 rests on.

This is NOT T393's `00-verify-t382-counts.py` re-run. It is a second implementation, written
without reading that file's selector, using different primitives on purpose:

  * populations come from `git ls-tree -r --name-only <ref> -- <dir>` with the OBSERVATION
    DIRECTORIES NAMED ON THE COMMAND LINE (T393 lists the whole capture directory and filters
    the first path component in Python). If either spelling silently selected the wrong set,
    the two would disagree.
  * the manifest is parsed by a different parser (awk-shaped split, explicit `*` strip).
  * digests are recomputed with hashlib over bytes read from disk, and separately compared to
    `git hash-object` for a sample, so a wrong hash function would show.

Exit 0 iff every asserted number reproduces. Exit 1 on ANY disagreement — a number that
disagrees must not be readable as a pass.

P-25: no floating point. Every number here is a len() or a hex digest.
P-24: the baseline is the LITERAL immutable sha, never a merge-base.
"""
import hashlib
import os
import pathlib
import subprocess
import sys

ROOT = os.environ.get("T423_ROOT") or str(pathlib.Path(__file__).resolve().parents[4])
REF = os.environ.get("T423_REF", "softhouse/T393-t382-conditions")
FORK = "12a7f8d9a3af4665fd5281a9f9c001d4f1276a53"
CAP = ".softhouse/capture/tierA-a2"
OBS = ("out", "req")

bad = []


def assert_eq(label, got, want):
    ok = got == want
    print("  %s  %-62s got=%s want=%s" % ("PASS" if ok else "FAIL", label, got, want))
    if not ok:
        bad.append(label)


def git(*a):
    return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, check=True).stdout


def lstree(ref, *paths):
    out = git("ls-tree", "-r", "--name-only", ref, "--", *paths).decode()
    return sorted(x for x in (l.strip() for l in out.split("\n")) if x)


def manifest_rows(blob):
    rows = {}
    for raw in blob.decode("utf-8").splitlines():
        s = raw.strip()
        if not s or s[0] == "#":
            continue
        bits = s.split()
        if len(bits) < 2:
            continue
        digest = bits[0]
        name = " ".join(bits[1:])
        if name.startswith("*"):
            name = name[1:]
        rows[name] = digest
    return rows


def sha256_file(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


print("=== T423 INDEPENDENT COUNTS ===")
print("ROOT %s" % ROOT)
print("REF  %s -> %s" % (REF, git("rev-parse", REF).decode().strip()))
print("FORK %s" % FORK)
print()

print("--- 1. populations, by ls-tree with the observation dirs NAMED ---")
obs_dirs_cli = [CAP + "/" + d for d in OBS]
fork_obs = lstree(FORK, *obs_dirs_cli)
head_obs = lstree(REF, *obs_dirs_cli)
assert_eq("ARM A population at the fork sha", len(fork_obs), 403)
assert_eq("ARM B population at the ref", len(head_obs), 1035)
assert_eq("fork set is a SUBSET of the ref set", set(fork_obs) <= set(head_obs), True)
post_fork = sorted(set(head_obs) - set(fork_obs))
assert_eq("post-fork observations (ref minus fork)", len(post_fork), 632)
assert_eq("403 + 632 == 1035", len(fork_obs) + len(post_fork), len(head_obs))

# cross-check the selector: whole-directory listing filtered in Python must agree
whole = lstree(REF, CAP)
py_filtered = sorted(p for p in whole
                     if p.startswith(CAP + "/")
                     and p[len(CAP) + 1:].split("/")[0] in OBS)
assert_eq("cli-named selector == python-filtered selector (ref)",
          py_filtered == head_obs, True)
whole_fork = lstree(FORK, CAP)
py_filtered_fork = sorted(p for p in whole_fork
                          if p.startswith(CAP + "/")
                          and p[len(CAP) + 1:].split("/")[0] in OBS)
assert_eq("cli-named selector == python-filtered selector (fork)",
          py_filtered_fork == fork_obs, True)
print("      tracked under %s at ref  : %d" % (CAP, len(whole)))
print("      tracked under %s at fork : %d" % (CAP, len(whole_fork)))

print()
print("--- 2. the manifest at the ref ---")
man = manifest_rows(git("show", REF + ":" + CAP + "/MANIFEST.sha256"))
man_obs = {k: v for k, v in man.items() if k.split("/")[0] in OBS}
assert_eq("MANIFEST.sha256 total rows", len(man), 1139)
assert_eq("MANIFEST rows under out/ or req/", len(man_obs), 1035)
assert_eq("MANIFEST rows NOT under out/ or req/", len(man) - len(man_obs), 104)
tracked_rel = set(p[len(CAP) + 1:] for p in head_obs)
assert_eq("tracked observations with NO manifest row", len(tracked_rel - set(man_obs)), 0)
assert_eq("manifest rows naming NO tracked observation", len(set(man_obs) - tracked_rel), 0)
assert_eq("row-set == tracked-set (T393's ARM C equality)", set(man_obs) == tracked_rel, True)
assert_eq("MANIFEST rows == tracked capture files minus MANIFEST itself",
          len(man), len(whole) - 1)
assert_eq("MANIFEST.sha256 has no row for ITSELF", "MANIFEST.sha256" in man, False)

print()
print("--- 3. every manifest digest recomputed from disk ---")
agree = disagree = unreadable = 0
first_bad = []
for name, want in sorted(man.items()):
    p = os.path.join(ROOT, CAP, name)
    try:
        got = sha256_file(p)
    except OSError as exc:
        unreadable += 1
        first_bad.append((name, repr(exc)))
        continue
    if got == want:
        agree += 1
    else:
        disagree += 1
        first_bad.append((name, "%s != %s" % (got, want)))
print("      agree=%d disagree=%d unreadable=%d" % (agree, disagree, unreadable))
for n, d in first_bad[:10]:
    print("        BAD %s  %s" % (n, d))
assert_eq("all 1139 manifest digests agree with disk", (agree, disagree, unreadable),
          (1139, 0, 0))
obs_agree = sum(1 for n in man_obs if sha256_file(os.path.join(ROOT, CAP, n)) == man_obs[n])
assert_eq("of which under out/ or req/", obs_agree, 1035)
covered = sum(1 for p in post_fork if p[len(CAP) + 1:] in man_obs)
assert_eq("post-fork observations covered by a manifest row", covered, 632)

print()
print("--- 4. the fork-sha manifest and ARM E's population ---")
fman = manifest_rows(git("show", FORK + ":" + CAP + "/MANIFEST.sha256"))
fnon = sorted(k for k in fman if k.split("/")[0] not in OBS)
assert_eq("fork-sha manifest total rows", len(fman), 430)
assert_eq("of those under out/ or req/", len(fman) - len(fnon), 403)
assert_eq("ARM E population (NOT under out/ or req/)", len(fnon), 27)
same = []
diff = []
for name in fnon:
    blob = git("show", FORK + ":" + CAP + "/" + name)
    h_fork = hashlib.sha256(blob).hexdigest()
    h_now = sha256_file(os.path.join(ROOT, CAP, name))
    (same if h_fork == h_now else diff).append(name)
print("      byte-identical to the fork sha : %d" % len(same))
print("      DIFFERING                      : %d  %s" % (len(diff), diff))
assert_eq("of the 27, byte-identical to the fork sha today", len(same), 25)
assert_eq("the differing set is EXACTLY {CAPTURE-PLAN.md, cap.sh}",
          sorted(diff), ["CAPTURE-PLAN.md", "cap.sh"])

print()
print("--- 5. hash-function cross-check (a wrong digest fn would pass §3 self-consistently) ---")
# git hash-object is a *different* implementation of a *different* hash, so it cannot confirm
# sha256 values; instead confirm hashlib against the coreutils shasum for three real files.
sample = sorted(man_obs)[:3]
for name in sample:
    p = os.path.join(ROOT, CAP, name)
    ours = sha256_file(p)
    ext = subprocess.run(["shasum", "-a", "256", p], capture_output=True,
                         check=True).stdout.decode().split()[0]
    assert_eq("shasum agrees with hashlib on %s" % name, ours, ext)

print()
print("FAILURES: %d" % len(bad))
for b in bad:
    print("  - " + b)
sys.exit(1 if bad else 0)
