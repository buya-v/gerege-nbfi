#!/usr/bin/env python3
"""
T234 — THE SOUND INSTRUMENT, and the re-run of every voided/unreproducible sweep.

WHY python3 `re` and not a grep:
  * one engine, one documented semantics for \\b \\d \\s \\w -- no -E/-P/-G fork;
  * MULTI-LINE capable, which closes T227's FU-T227-2: every sweep in this chain,
    T227's and T232's included, is line-oriented, and T224's missed site straddled
    a line break.  A line-oriented matcher cannot see a claim split over two lines.
  * corpus is read from `git cat-file`, so it works at ANY rev, including revs whose
    worktree has been deleted -- which is exactly why A2-31/A2-32/A2-33's sweeps
    cannot be re-run (they hard-`cd` into worktrees that no longer exist).

CALIBRATION (P-72) IS MANDATORY AND RUNS FIRST.  The instrument is pointed at a
KNOWN POSITIVE before any negative it reports is allowed to mean anything.

Usage: 30-sound-sweep.py <rev>
"""
import re, subprocess, sys, json, collections, os

ROOT = subprocess.run(["git","rev-parse","--show-toplevel"],capture_output=True,text=True).stdout.strip()
os.chdir(ROOT)
REV = sys.argv[1] if len(sys.argv)>1 else "HEAD"
SELF = ".softhouse/capture/t234-sweep-instrument-audit/"

def tracked(rev):
    return [f for f in subprocess.run(["git","ls-tree","-r","--name-only",rev],
            capture_output=True,text=True).stdout.split("\n") if f]

def blob(rev,f):
    r = subprocess.run(["git","show",f"{rev}:{f}"],capture_output=True)
    return r.stdout.decode("utf-8","replace") if r.returncode==0 else None

# ---------------------------------------------------------------- T224's NINE TERMS
# Transcribed from .softhouse/handoff/.../T224.md:78-96.  T224 committed NO SCRIPT,
# so these are its PROSE terms, literally as written -- which is all anyone can audit.
T224_TERMS = [
 ("T1", r'(is |are |were |has not been |)not checked'),
 ("T2", r'no such guard'),
 ("T3", r'does not exist'),
 ("T4", r'did not exist'),
 ("T5", r'nothing checks'),
 ("T6", r'no guard for either'),
 ("T7", r'unguarded|no source guard|not enforced|is not enforced|no enforcement'),
 ("T8", r'\bnot exist\b'),
 ("T9", r'(guard|invariant|ledger|I-3|I-4).{0,120}(\bexist\b|checked|no such|nothing checks)'),
]

# ---------------------------------------------------------------- THE SOUND NET
# Same CONCEPT (P-26), built to the rules T232/P-72 derived:
#  * NEVER right-anchor an inflected stem  -> exist matches existing/exists/existed/existence
#  * DOTALL + the newline explicitly inside the gap -> multi-line, closes FU-T227-2
#  * case-insensitive: the surviving site was SHOUTED ("records as NOT EXISTING")
GAP = r'[\s\S]{0,160}'
SUBJ = r'(guard|ledgerguard|invariant|I-?3|I-?4|check|enforce|ledger)'
ABSENT = r'(not\s+exist\w*|non-?exist\w*|does\s+not\s+exist\w*|no\s+such|nothing\s+check\w*|'\
         r'not\s+check\w*|un-?checked|un-?guarded|not\s+enforce\w*|no\s+enforcement|absent|missing)'
SOUND_NET = [
 ("S1-fwd",  SUBJ+GAP+ABSENT),
 ("S2-rev",  ABSENT+GAP+SUBJ),
 ("S3-bare", r'not\s+exist\w*'),           # deliberately NOT right-anchored
 ("S4-4.4.1",r'4\.4\.1'+GAP+r'(not\s+exist\w*|no\s+guard|absent)'),
 ("S5-recs", r'record\w*\s+(it\s+)?as\s+not\s+exist\w*'),
 ("S6-noguard", r'no\s+guard\s+for\s+(either|I-?3|I-?4|both)'),
]

def scan(rev, terms, files=None, flags=re.I):
    """returns {termid: [(file, lineno, excerpt)]}. MULTI-LINE: offsets mapped back to lines."""
    if files is None: files = tracked(rev)
    comp = [(t, re.compile(p, flags)) for t,p in terms]
    out = collections.defaultdict(list)
    for f in files:
        b = blob(rev,f)
        if b is None or "\x00" in b[:4096]: continue
        if len(b) > 4_000_000: continue
        starts = [0]
        for ch in b:
            pass
        # line index
        nl = [i for i,c in enumerate(b) if c=="\n"]
        def lineno(off):
            lo,hi=0,len(nl)
            while lo<hi:
                mid=(lo+hi)//2
                if nl[mid]<off: lo=mid+1
                else: hi=mid
            return lo+1
        for t,c in comp:
            for m in c.finditer(b):
                out[t].append((f, lineno(m.start()), b[m.start():m.end()][:180].replace("\n","\\n")))
    return out

# ================================================================= CALIBRATION FIRST
print("="*78)
print("CALIBRATION (P-72) — point the instrument at a KNOWN POSITIVE before believing a negative")
print("="*78)
CAL_REV, CAL_FILE = "90c21d6", ".softhouse/guards/ledgerguard/main.go"
cb = blob(CAL_REV, CAL_FILE)
if cb is None:
    print("  !! calibration blob unavailable at", CAL_REV, "-- CALIBRATION FAILED, negatives below mean NOTHING")
else:
    print(f"  known positive: {CAL_REV}:{CAL_FILE} line 1")
    print("  literal text  :", repr(cb.splitlines()[0]))
    r24 = scan(CAL_REV, T224_TERMS, [CAL_FILE])
    hit24 = [t for t,_ in T224_TERMS if any(l==1 for _,l,_ in r24.get(t,[]))]
    print(f"  T224's 9 terms, recall on line 1 : {len(hit24)}/9   hits={hit24 or 'NONE'}")
    rs = scan(CAL_REV, SOUND_NET, [CAL_FILE])
    hits = [t for t,_ in SOUND_NET if any(l==1 for _,l,_ in rs.get(t,[]))]
    print(f"  SOUND NET, recall on line 1      : {len(hits)}/{len(SOUND_NET)}  hits={hits}")
    print("  CALIBRATION VERDICT:", "PASS - instrument fires on the known positive" if hits
          else "FAIL - DO NOT TRUST ANY NEGATIVE BELOW")
    # second known positive: the site T224 itself fixed
    CAL2 = ".softhouse/conformance.sh"
    c2 = blob(CAL_REV, CAL2)
    if c2:
        seg = "\n".join(c2.splitlines()[1112:1118])
        print(f"\n  known positive 2: {CAL_REV}:{CAL2}:1113-1118 (the site T224 was HANDED)")
        for ln in seg.splitlines(): print("     |", ln.strip()[:120])
        r2 = scan(CAL_REV, T224_TERMS, [CAL2])
        in2 = [t for t,_ in T224_TERMS if any(1110<=l<=1120 for _,l,_ in r2.get(t,[]))]
        s2 = scan(CAL_REV, SOUND_NET, [CAL2])
        in2s = [t for t,_ in SOUND_NET if any(1110<=l<=1120 for _,l,_ in s2.get(t,[]))]
        print(f"  T224's 9 terms recall there : {len(in2)}/9  {in2 or 'NONE'}")
        print(f"  SOUND NET recall there      : {len(in2s)}/{len(SOUND_NET)}  {in2s}")

# ================================================================= LIVE RE-RUN
print()
print("="*78)
print(f"LIVE RE-RUN of the sound net over ALL TRACKED CONTENT at {REV}")
print("="*78)
files = tracked(REV)
print("  corpus:", len(files), "tracked files (whole repo, not just .softhouse)")
res = scan(REV, SOUND_NET, files)
tot = collections.Counter()
for t,_ in SOUND_NET:
    print("  %-10s hits=%d  in %d files" % (t, len(res.get(t,[])), len(set(f for f,_,_ in res.get(t,[])))))
json.dump({t:res.get(t,[]) for t,_ in SOUND_NET},
          open(SELF+f"evidence/sound-sweep-{REV.replace('/','_')}.json","w"), indent=1)
print("  full hit list -> evidence/sound-sweep-%s.json" % REV.replace('/','_'))

# the high-signal narrow classes only
print()
print("  --- S5 (records ... as not existing) and S6 (no guard for either): the retracted CLAIM verbatim ---")
for t in ("S5-recs","S6-noguard"):
    for f,l,x in res.get(t,[]):
        print("    %-6s %s:%s  %s" % (t,f,l,x[:130]))
