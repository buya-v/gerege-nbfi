#!/usr/bin/env python3
"""T456 -- INDEPENDENT re-derivation of T451's "705 live refs / 84 pairs / exactly 0".

DELIBERATELY A DIFFERENT PRIMITIVE.  T451's bin/20 and bin/21 read the ref store through
`branch_sweep.RefIndex`, a filesystem walk of `refs/heads` + `packed-refs`.  This one
reads it through `git for-each-ref`, and it re-implements the two anchors from the
regex definitions in `id_pattern()` rather than importing them.  T448's rule: two
derivations that share a primitive are one derivation.

It also prints, on every run, the FAIL-CLOSED cardinals a reader needs to tell a
measured zero from a broken run: ref count, id count, pair count, and how many git
calls returned non-zero.  A zero in section B is only interpretable beside them.

Usage:  python3 <this file> [--full]
"""
import re
import subprocess
import sys

REPO = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True).stdout.strip()
GIT_ERRORS = []


def g(*a):
    p = subprocess.run(["git", "-C", REPO] + list(a), capture_output=True, text=True)
    if p.returncode != 0:
        GIT_ERRORS.append((a[:2], p.returncode, p.stderr.strip()[:120]))
    return p.returncode, p.stdout, p.stderr


def short(n):
    return n[len("refs/heads/"):] if n.startswith("refs/heads/") else n


IDRE = re.compile(r"(?<![0-9A-Za-z])([Tt][0-9]+)(?![0-9A-Za-z])")


def ids_in(name):
    return set(m.group(1).upper() for m in IDRE.finditer(short(name)))


def pats(tid):
    """Re-implemented from ready-tasks.py id_pattern()'s two regexes."""
    return (re.compile(r"(?<![0-9A-Za-z])" + re.escape(tid) + r"(?![0-9A-Za-z])", re.I),
            re.compile(re.escape(tid) + r"(?![0-9A-Za-z])", re.I))


def evidence(tid, ref, anchor):
    """(carries|None, hits, mentions).  None means a git call did not answer -- an
    UNPROBED result, never a negative."""
    anywhere, leading = pats(tid)
    rc, out, _ = g("log", "--format=%H%x09%s", "main..%s" % ref)
    if rc != 0:
        return None, ["log rc=%s" % rc], []
    hits = []
    for line in out.splitlines():
        sha, _, subj = line.partition("\t")
        if anywhere.search(subj):
            hits.append("commit %s subject %r" % (sha[:9], subj[:78]))
    rc2, out2, _ = g("diff", "--name-only", "main...%s" % ref)
    if rc2 != 0:
        return None, ["diff rc=%s" % rc2], []
    mentions = []
    for path in out2.splitlines():
        parts = path.split("/")
        if anchor == "leading":
            own = any(leading.match(p) for p in parts)
        else:
            own = any(anywhere.search(p) for p in parts)
        if own:
            hits.append("path %s" % path)
        elif any(anywhere.search(p) for p in parts):
            mentions.append(path)
    return (len(hits) > 0), hits, mentions


def main():
    rc, out, _ = g("for-each-ref", "--format=%(refname)", "refs/heads")
    heads = sorted(out.splitlines())
    rc_all, out_all, _ = g("for-each-ref", "--format=%(refname)")
    print("HEAD of this worktree                  :",
          g("rev-parse", "--short", "HEAD")[1].strip())
    print("main at                                :",
          g("rev-parse", "--short", "main")[1].strip())
    print("ALL refs (any namespace)               :", len(out_all.splitlines()))
    print("refs/heads only  <-- the population    :", len(heads))
    if not heads:
        print("ABORT: zero refs. A census over nothing proves nothing (P-35).")
        return 91

    id_to_refs = {}
    for n in heads:
        for i in ids_in(n):
            id_to_refs.setdefault(i, []).append(n)
    incidences = sum(len(v) for v in id_to_refs.values())
    print("ids nameable from a head               :", len(id_to_refs))
    print("(id, own-head) incidences              :", incidences)

    pairs = set()
    for i, refs in id_to_refs.items():
        for own in refs:
            for other in refs:
                if other != own:
                    pairs.add((i, other))
    pairs = sorted(pairs)
    print("(id, other-ref) pairs  <-- probes      :", len(pairs))

    fan = {}
    for i, refs in id_to_refs.items():
        for _own in refs:
            k = len(refs) - 1
            fan[k] = fan.get(k, 0) + 1
    print("fan-out histogram                      :", dict(sorted(fan.items())))
    print("MAX fan-out on this repo today         :", max(fan) if fan else 0)

    ship, only_relaxed, neither, unprobed = [], [], [], []
    for (i, ref) in pairs:
        c1, w1, _m1 = evidence(i, ref, "leading")
        c2, w2, _m2 = evidence(i, ref, "anywhere")
        if c1 is None or c2 is None:
            unprobed.append((i, ref))
            continue
        if c1:
            ship.append((i, ref, w1))
        elif c2:
            only_relaxed.append((i, ref, w2))
        else:
            neither.append((i, ref))

    print()
    print("A. CARRY under SHIPPED  (leading) :", len(ship))
    for i, ref, w in ship:
        owners = sorted(ids_in(ref))
        lead = short(ref).split("/")[-1]
        m = IDRE.match(lead) or IDRE.search(lead)
        owner = (m.group(1).upper() if m else "?")
        tag = "own" if owner == i else "FOREIGN"
        print("   %-6s %-50s owner=%-6s %s" % (i, short(ref), owner, tag))
        print("        %s" % (w[0][:140] if w else ""))
    print("B. CARRY only under RELAXED (anywhere) -- WHAT T449's PATCH ADDS :",
          len(only_relaxed))
    for i, ref, w in only_relaxed:
        print("   %-6s %-50s %s" % (i, short(ref), w[0][:120] if w else ""))
    print("C. name-only under BOTH           :", len(neither))
    print("D. UNPROBED (a git call refused)  :", len(unprobed), unprobed[:5])
    print()
    print("git calls that returned non-zero  :", len(GIT_ERRORS), GIT_ERRORS[:3])
    print("INTERPRETABILITY: section B's number is a MEASURED zero only if D and the")
    print("non-zero git-call count are both 0 and the pair count above is non-zero.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
