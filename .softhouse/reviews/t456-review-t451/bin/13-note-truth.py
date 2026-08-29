#!/usr/bin/env python3
"""T456 -- C-T449-1's second half: the RECORD, not just the verdict.

The founding defect of T350 is a note that says the reverse of the truth.  T451's
handoff claims the new `stillborn-carried` note "names the ref, names the path, says
'BUT IT IS NOT UNSTARTED', and tells the reader to run branch_sweep.py sweep".  A
verdict that agrees with G2 while carrying a false sentence would still be the T350
defect.  So each ASSERTION in the emitted note is checked against git.

Also checks the negative direction: case N (a NAME-ONLY ref beside a parked branch) must
keep DEMOTING, and its note must NOT claim no ref exists.

usage: 13-note-truth.py <green.py> <fixture-dir>
"""
import importlib.util
import re
import subprocess
import sys

GREEN, FIX = sys.argv[1], sys.argv[2]


def g(*a):
    return subprocess.run(["git", "-C", FIX] + list(a), capture_output=True, text=True)


spec = importlib.util.spec_from_file_location("m_green", GREEN)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
if getattr(m, "branch_sweep", "x") is None:
    sys.exit("ABORT: branch_sweep not importable beside %s" % GREEN)
m.set_repo(FIX)

fails = 0
for BRANCH, TID, LABEL in (("softhouse/T900-work", "T900", "G  (parked + carrier)"),
                           ("softhouse/T901-work", "T901", "G2 (deleted + carrier)")):
    m._MAINTREE = ("uncached", None)
    m._REF_INDEX = ("uncached", None)
    m._IDPAT = {}
    kind, text = m.branch_wip(BRANCH, TID)
    action = m.reconcile_action(kind)
    pol = "REFUSE" if action.startswith("REFUSE") else "demote"
    print("=" * 88)
    print("%s   kind=%s   polarity=%s" % (LABEL, kind, pol))
    print("-" * 88)
    print(text)
    print("-" * 88)

    # --- ASSERTION 1: every ref the note names must EXIST and must actually carry.
    # NOT preceded by a dot: `.softhouse/bin/x.py` is a PATH, `softhouse/T900-work` is
    # a REF.  The first version of this instrument matched both and reported 6 false
    # "FALSE" rows -- a reviewer instrument fabricating findings, caught here and fixed
    # rather than shipped.
    named_refs = set(re.findall(r"(?<![.\w])softhouse/[A-Za-z0-9._/-]+", text))
    named_refs = {r.rstrip(".,;`'\"") for r in named_refs}
    named_refs = {r for r in named_refs if not r.endswith("*")}
    checked = 0
    for r in sorted(named_refs):
        p = g("rev-parse", "-q", "--verify", "refs/heads/" + r)
        exists = p.returncode == 0
        if r == BRANCH:
            continue
        checked += 1
        d = g("diff", "--name-only", "main...refs/heads/" + r)
        anywhere = re.compile(r"(?<![0-9A-Za-z])" + TID + r"(?![0-9A-Za-z])", re.I)
        leading = re.compile(TID + r"(?![0-9A-Za-z])", re.I)
        owns = [pp for pp in d.stdout.splitlines()
                if any(leading.match(c) for c in pp.split("/"))]
        print("  ref named in the note: %-46s exists=%s owns=%s"
              % (r, exists, owns or "[]"))
        if not exists:
            print("     *** FALSE: the note names a ref that does not resolve")
            fails += 1
        elif "CARRY CONTENT" in text and not owns:
            print("     *** FALSE: the note says CARRY CONTENT and no path is owned")
            fails += 1
    if checked == 0 and "CARRY CONTENT" in text:
        print("  *** the note claims a carrier but names no ref -- unverifiable")
        fails += 1

    # --- ASSERTION 2: every repo path the note names must be in that ref's diff.
    # Paths inside a backticked RECOVERY COMMAND are not claims about the ref's diff;
    # they are an instruction to the reader, checked separately by ASSERTION 3. Strip
    # them first -- the previous version counted `.softhouse/bin/branch_sweep.py` from
    # the sweep command as a false claim, which was MY defect, not the note's.
    body = re.sub(r"`[^`]*`", "``", text)
    paths = re.findall(r"(?:^|[ (])((?:\.softhouse|\.git)[A-Za-z0-9._/-]+)", body)
    for p_ in sorted(set(paths)):
        found = [r for r in named_refs
                 if p_ in g("diff", "--name-only", "main...refs/heads/" + r).stdout]
        print("  path named in the note: %-56s in ref(s) %s" % (p_, found or "NONE"))
        if not found:
            print("     *** FALSE: the note names a path no named ref carries")
            fails += 1

    # --- ASSERTION 3: the recovery command it prints must be a real, runnable one.
    cmds = re.findall(r"`(python3 [^`]+)`", text)
    print("  recovery command(s) printed: %s" % (cmds or "NONE"))
    if kind == "stillborn-carried":
        if not cmds:
            print("     *** the REFUSE note gives the reader no recovery command")
            fails += 1
        else:
            tool = cmds[0].split()[1]
            import os
            root = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                                  capture_output=True, text=True).stdout.strip()
            ok = os.path.exists(os.path.join(root, tool))
            print("     tool %s exists in THIS repo: %s" % (tool, ok))
            if not ok:
                fails += 1

    # --- ASSERTION 4: the sentence the old code got wrong must be gone.
    if "and it is UNSTARTED" in text and kind == "stillborn-carried":
        print("     *** FALSE: the note still asserts UNSTARTED beside a live carrier")
        fails += 1
    print()

# --- case N: name-only ref beside a parked branch. Action must stay DEMOTE, and the
#     note must NOT claim that no ref exists.
m._MAINTREE = ("uncached", None)
m._REF_INDEX = ("uncached", None)
m._IDPAT = {}
kind, text = m.branch_wip("softhouse/T990-shared-file", "T990")
print("=" * 88)
print("S/T990 (shared-file rescue: no id anywhere in the diff)   kind=%s   %s"
      % (kind, m.reconcile_action(kind)[:30]))
print(text[:1200])
if "no live ref carries id T990 in its name either" in text:
    print("\n  NOTE: for T990 the ref IS named `rescued-t990-shared-file-...`, so a note")
    print("  saying no ref carries the id IN ITS NAME would be FALSE. Checking...")
    idx = m.refs_naming("T990", "softhouse/T990-shared-file")
    print("  refs_naming('T990') -> %s" % (idx[0],))
    if idx[0]:
        print("     *** FALSE: refs DO name T990 and the note says none do")
        fails += 1
# ---------------------------------------------------------------- P-22 RED LEG
# A checker that has only ever printed 0 is not a checker. Point it at RED -- main's
# bytes -- where case G's note asserts "it is UNSTARTED" while a live ref carries the
# work. If this leg does NOT flag, the checker above proves nothing.
print("=" * 88)
print("P-22 RED LEG -- the same assertion checked against main's bytes")
red = sys.argv[3] if len(sys.argv) > 3 else None
if not red:
    print("  SKIPPED: no <red.py> given. THIS INSTRUMENT IS UNCALIBRATED; the 0 above")
    print("  is not interpretable. Pass red.py as argv[3].")
    sys.exit(92)
rspec = importlib.util.spec_from_file_location("m_red", red)
mr = importlib.util.module_from_spec(rspec)
rspec.loader.exec_module(mr)
mr.set_repo(FIX)
mr._MAINTREE = ("uncached", None)
mr._REF_INDEX = ("uncached", None)
mr._IDPAT = {}
rkind, rtext = mr.branch_wip("softhouse/T900-work", "T900")
carrier = "softhouse/rescued-t900-work-20260829"
owns = g("diff", "--name-only", "main...refs/heads/" + carrier).stdout.split()
red_false = ("it is UNSTARTED" in rtext) and bool(owns)
print("  RED kind                     : %s" % rkind)
print("  RED note asserts UNSTARTED   : %s" % ("it is UNSTARTED" in rtext))
print("  a live ref carries T900 work : %s  %s" % (bool(owns), owns))
print("  RED LEG CAUGHT THE FALSEHOOD : %s" % red_false)
if not red_false:
    print("  *** CALIBRATION MISS: the checker could not detect a note that is known to")
    print("      be false. Every 0 above is uninterpretable.")
    sys.exit(92)
print()
print("=" * 88)
print("FALSE OR UNSUPPORTED ASSERTIONS IN GREEN: %d   (RED leg: 1, caught)" % fails)
sys.exit(1 if fails else 0)
