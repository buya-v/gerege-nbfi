#!/usr/bin/env python3
"""T279 — measure the two candidate answers to T265 F-2 against the SAME fire history
T265 used (`~/Library/Logs/gerege-nbfi/fire-*.log` + origin/main + the push reflog).

F-2: rule 2 reads `git log -1 --format=%ct origin/main` with no holder test, so the
freshness term is refreshed by third parties and the old rule's GUARANTEED EVENTUAL
TAKEOVER is gone.  T265 offered two repairs and told T279 to choose ONE and measure it:

  (A) AUTHOR-MATCH   restrict the push term to commits authored by the lock's holder.
  (B) CEILING        a lock whose `started_at` is over N h old is stale regardless.

The measurements this file makes, in order:

  1. reproduce T265 §4 -- at every real fire start, would a STRANDED lock read HELD under
     rule 2 as written?  (T265: 16 of 21.)
  2. AUTHOR-MATCH liveness: same 21 starts, with the push term restricted to the stranded
     holder's own identity.
  3. AUTHOR-MATCH SAFETY -- the measurement T265 did not make.  How many DISTINCT git
     identities publish inside a SINGLE fire window?  If a live fire routinely pushes
     under more than one name, and the LOCK records none of them, then author-match makes
     a LIVE holder read STALE -- which is not the liveness bug F-2 describes, it is the
     P-85 SAFETY bug itself, with the sign flipped.
  4. CEILING: the longest fire on record, which is the only thing a ceiling can be wrong
     about, and the margin at N = 24 h.
  5. CEILING liveness: at every fire start, would a lock stranded by the PREVIOUS fire be
     takeable under the ceiling?
"""
import collections
import datetime
import glob
import os
import re
import subprocess

SIX_H = 6 * 3600
CEILING_H = 24
CEILING = CEILING_H * 3600


def sh(*a):
    return subprocess.run(a, capture_output=True, text=True).stdout


def commits():
    cs = []
    for line in sh("git", "log", "--format=%ct|%h|%an <%ae>", "origin/main").splitlines():
        ct, h, who = line.split("|", 2)
        cs.append((int(ct), h, who))
    return sorted(cs)


def fires(min_secs=300):
    out = []
    for f in sorted(glob.glob(os.path.expanduser("~/Library/Logs/gerege-nbfi/fire-*.log"))):
        b = os.path.basename(f)
        try:
            st = datetime.datetime.strptime(b[5:-4], "%Y%m%d-%H%M%S").timestamp()
        except ValueError:
            continue
        en = os.path.getmtime(f)
        if en - st < min_secs:
            continue
        out.append((b, st, en))
    return out


def hh(s):
    return "%.2f h" % (s / 3600.0)


def main():
    cs, fs = commits(), fires()
    print("origin/main commits: %d   real fires (>=5 min): %d" % (len(cs), len(fs)))
    print("thresholds: rule-2 freshness 6 h, ceiling %d h\n" % CEILING_H)

    # ---------------------------------------------------------------- authors --
    au = collections.Counter(w for _c, _h, w in cs)
    print("--- 0. identities publishing to origin/main ---")
    for w, n in au.most_common():
        print("    %-52s %5d" % (w, n))
    print()

    # -------------------------------------------- 1. rule 2 as written (T265) --
    print("--- 1. rule 2 AS WRITTEN: stranded lock at every fire start ---")
    r1_held = 0
    rows = []
    for i, (b, st, en) in enumerate(fs):
        prev = [c for c in cs if c[0] < st]
        if not prev:
            continue
        age = st - prev[-1][0]
        held = age < SIX_H
        r1_held += held
        rows.append((b, st, en, age, held))
        print("    %-30s newest-by-anyone %8s   %s"
              % (b, hh(age), "HELD (idles)" if held else "takeable"))
    print("\n    %d of %d fire starts read a STRANDED lock as HELD.\n" % (r1_held, len(rows)))

    # ------------------------------------------------- 2. author-match liveness --
    print("--- 2. (A) AUTHOR-MATCH: same starts, push term restricted to the holder ---")
    print("    holder := the fire immediately preceding this start; its identity := the")
    print("    author of its LAST commit inside its own window.  A stranded holder never")
    print("    pushes again, so this term ages monotonically.")
    a_held = 0
    a_rows = 0
    for i, (b, st, en) in enumerate(fs):
        if i == 0:
            continue
        pb, pst, pen = fs[i - 1]
        inw = [c for c in cs if pst <= c[0] <= pen]
        if not inw:
            print("    %-30s (previous fire published nothing -- unattributable)" % b)
            continue
        who = inw[-1][2]
        mine = [c for c in cs if c[0] < st and c[2] == who]
        age = st - mine[-1][0]
        held = age < SIX_H
        a_held += held
        a_rows += 1
        print("    %-30s holder %-34s newest-by-holder %8s  %s"
              % (b, who.split(" <")[0], hh(age), "HELD" if held else "takeable"))
    print("\n    %d of %d starts read a STRANDED lock as HELD under author-match.\n"
          % (a_held, a_rows))

    # ------------------------------------------------ 3. author-match SAFETY ----
    print("--- 3. (A) AUTHOR-MATCH SAFETY: distinct identities inside ONE LIVE fire ---")
    multi = 0
    tot = 0
    for b, st, en in fs:
        inw = [c for c in cs if st <= c[0] <= en]
        if not inw:
            continue
        tot += 1
        ids = collections.Counter(c[2] for c in inw)
        if len(ids) > 1:
            multi += 1
        print("    %-30s %2d commits, %d identit%s: %s"
              % (b, len(inw), len(ids), "y" if len(ids) == 1 else "ies",
                 "; ".join("%s x%d" % (k.split(" <")[0], v) for k, v in ids.most_common())))
    print("\n    %d of %d fires that published anything did so under MORE THAN ONE identity."
          % (multi, tot))
    print("    The LOCK body records `holder`, `host`, `pid`, `fire` -- and NO git identity,")
    print("    so author-match has nothing to match against today; it must first be given a")
    print("    field, and that field can only name ONE of the identities measured above.\n")

    # ------------------------------------------------------- 4. ceiling cost ----
    print("--- 4. (B) CEILING: what a ceiling can be wrong about is a LONG LEGITIMATE fire ---")
    durs = sorted(((en - st, b) for b, st, en in fs), reverse=True)
    for d, b in durs[:5]:
        print("    %-30s ran %8s" % (b, hh(d)))
    longest = durs[0][0]
    print("    longest fire on record: %s   ceiling %d h   margin %.2fx\n"
          % (hh(longest), CEILING_H, CEILING / longest))

    # --------------------------------------------------- 5. ceiling liveness ----
    print("--- 5. (B) CEILING liveness: lock stranded by the PREVIOUS fire ---")
    c_held = 0
    c_rows = 0
    for i, (b, st, en) in enumerate(fs):
        if i == 0:
            continue
        pb, pst, _pen = fs[i - 1]
        lock_age = st - pst
        prev = [c for c in cs if c[0] < st]
        tip_age = st - prev[-1][0] if prev else 10 ** 9
        # repaired arms N3 / N4 / N5 / N6, dead-pid arm excluded (cross-host case)
        if lock_age >= CEILING:
            v, why = "takeable", "N3 ceiling"
        elif tip_age < SIX_H:
            v, why = "HELD", "N4 live"
        elif lock_age >= SIX_H:
            v, why = "takeable", "N5 both stale"
        else:
            v, why = "HELD", "N6 default"
        c_held += (v == "HELD")
        c_rows += 1
        print("    %-30s lock age %8s  tip age %8s  -> %-8s (%s)"
              % (b, hh(lock_age), hh(tip_age), v, why))
    print("\n    %d of %d read HELD under the repaired arms." % (c_held, c_rows))
    print("    Under the ceiling the takeover time is BOUNDED at started_at + %d h for every"
          % CEILING_H)
    print("    one of them; under rule 2 as written there is no bound at all.\n")

    # ------------------------------- 6. head-to-head, verdict by verdict --------
    print("--- 6. HEAD TO HEAD: at how many real fire starts does each repair CHANGE the")
    print("       verdict rule 2 as written would have given? ---")
    d_author = d_ceiling = n = 0
    changed = []
    for i, (b, st, en) in enumerate(fs):
        if i == 0:
            continue
        pb, pst, pen = fs[i - 1]
        prev = [c for c in cs if c[0] < st]
        if not prev:
            continue
        inw = [c for c in cs if pst <= c[0] <= pen]
        if not inw:
            continue
        n += 1
        base = "HELD" if (st - prev[-1][0]) < SIX_H else "takeable"
        who = inw[-1][2]
        mine = [c for c in cs if c[0] < st and c[2] == who]
        auth = "HELD" if (st - mine[-1][0]) < SIX_H else "takeable"
        lock_age = st - pst
        if lock_age >= CEILING:
            ceil = "takeable"
        elif (st - prev[-1][0]) < SIX_H:
            ceil = "HELD"
        elif lock_age >= SIX_H:
            ceil = "takeable"
        else:
            ceil = "HELD"
        if auth != base:
            d_author += 1
            changed.append((b, "author-match", base, auth))
        if ceil != base:
            d_ceiling += 1
            changed.append((b, "ceiling", base, ceil))
    for b, k, a, c in changed:
        print("    %-30s %-13s %s -> %s" % (b, k, a, c))
    if not changed:
        print("    (none)")
    print("\n    (A) AUTHOR-MATCH changes the verdict at %d of %d real fire starts." % (d_author, n))
    print("    (B) CEILING       changes the verdict at %d of %d real fire starts." % (d_ceiling, n))


if __name__ == "__main__":
    main()
