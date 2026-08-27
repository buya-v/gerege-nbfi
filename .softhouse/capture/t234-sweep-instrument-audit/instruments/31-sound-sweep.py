#!/usr/bin/env python3
"""
T234 — THE SOUND INSTRUMENT.  (Fast rewrite of 30-sound-sweep.py, which spawned one
`git show` per file and was killed at >4 min.  Worktree files are now read directly;
`git show` is used only for the two historical calibration blobs at 90c21d6.)

ENGINE: python3 `re`, stated per P-53 rule 1.  Chosen because:
  * ONE documented semantics for \\b \\d \\s \\w -- no -E/-P/-G fork, no BSD/GNU/ugrep fork;
  * MULTI-LINE by construction ([\\s\\S] gaps, offsets mapped back to line numbers).
    This closes T227's FU-T227-2: every sweep in this chain -- T224's, T227's, T232's,
    A2-31/32/33's -- is LINE-ORIENTED, and T224's missed site straddled a line break.
    A multi-line matcher has never been run against this repo before this file.
  * reads the WORKTREE, so it is NOT blind to .gitignore'd paths the way the Bash-tool
    `grep` function is (P-131 in patterns.md ~line 707: --ignore-files honours
    .gitignore, which lists .claude/worktrees/).

CALIBRATION (P-72) RUNS FIRST AND ITS VERDICT GATES EVERYTHING BELOW.
"""
import re, subprocess, sys, json, collections, os

ROOT = subprocess.run(["git","rev-parse","--show-toplevel"],capture_output=True,text=True).stdout.strip()
os.chdir(ROOT)
SELF = ".softhouse/capture/t234-sweep-instrument-audit/"
CAL_REV = "90c21d6"

def tracked():
    return [f for f in subprocess.run(["git","ls-files"],capture_output=True,text=True).stdout.split("\n") if f]

def blob_at(rev,f):
    r = subprocess.run(["git","show",f"{rev}:{f}"],capture_output=True)
    return r.stdout.decode("utf-8","replace") if r.returncode==0 else None

def read(f):
    try:
        with open(f,"rb") as fh: b=fh.read()
    except Exception: return None
    if b"\x00" in b[:8192] or len(b)>4_000_000: return None
    return b.decode("utf-8","replace")

# ---- T224's NINE TERMS, transcribed from T224.md:78-96.  T224 committed NO SCRIPT.
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

# ---- THE SOUND NET.  Same CONCEPT (P-26); built to P-72's rules:
#      never right-anchor an inflected stem; gaps cross newlines; case-insensitive.
GAP    = r'[\s\S]{0,160}'
SUBJ   = r'(guard|ledgerguard|invariant|I-?3\b|I-?4\b|enforce|ledger)'
ABSENT = (r'(not\s+exist\w*|non-?exist\w*|no\s+such\s+guard|nothing\s+check\w*|'
          r'not\s+check\w*|un-?checked|un-?guarded|not\s+enforce\w*|no\s+enforcement)')
SOUND_NET = [
 ("S1-fwd",     SUBJ+GAP+ABSENT),
 ("S2-rev",     ABSENT+GAP+SUBJ),
 ("S3-bare",    r'not\s+exist\w*'),
 ("S4-441",     r'4\.4\.1'+GAP+r'(not\s+exist\w*|no\s+guard|absent)'),
 ("S5-records", r'record\w*\s+(it\s+)?as\s+not\s+exist\w*'),
 ("S6-noguard", r'no\s+guard\s+for\s+(either|I-?3|I-?4|both)'),
]

def linemap(b):
    nl=[i for i,c in enumerate(b) if c=="\n"]
    def f(off):
        lo,hi=0,len(nl)
        while lo<hi:
            m=(lo+hi)//2
            if nl[m]<off: lo=m+1
            else: hi=m
        return lo+1
    return f

def scan_text(txt, terms):
    lm=linemap(txt); out=collections.defaultdict(list)
    for t,p in terms:
        for m in re.compile(p, re.I).finditer(txt):
            out[t].append((lm(m.start()), txt[m.start():m.end()][:200].replace("\n","\\n")))
    return out

# ======================================================= CALIBRATION
print("="*80)
print("CALIBRATION (P-72) — the instrument is pointed at KNOWN POSITIVES first.")
print("Engine for every number below: python3 re, %s (P-53 rule 1)."%sys.version.split()[0])
print("="*80)
CAL_OK=False
for cf, want_line, why in [
    (".softhouse/guards/ledgerguard/main.go", 1, "the survivor T224 MISSED (A2-18 wrote it)"),
    (".softhouse/conformance.sh", 1116, "the site T224 was HANDED BY LINE NUMBER and fixed")]:
    b = blob_at(CAL_REV, cf)
    print("\n  known positive: %s:%s @ %s  -- %s"%(cf,want_line,CAL_REV,why))
    if b is None:
        print("    !! blob unavailable -- CALIBRATION INCOMPLETE"); continue
    ls=b.splitlines()
    print("    text: %r"%(ls[want_line-1].strip()[:150] if len(ls)>=want_line else "??"))
    r24=scan_text(b,T224_TERMS); rs=scan_text(b,SOUND_NET)
    near=lambda d: [t for t,_ in d[0] if any(abs(l-want_line)<=2 for l,_ in d[1].get(t,[]))]
    h24=[t for t,_ in T224_TERMS if any(abs(l-want_line)<=2 for l,_ in r24.get(t,[]))]
    hs =[t for t,_ in SOUND_NET  if any(abs(l-want_line)<=2 for l,_ in rs.get(t,[]))]
    print("    T224's 9 prose terms, recall here : %d/9   %s"%(len(h24), h24 or "NONE"))
    print("    T234 SOUND NET,       recall here : %d/%d  %s"%(len(hs),len(SOUND_NET), hs or "NONE"))
    if hs: CAL_OK=True
print("\n  CALIBRATION VERDICT: %s"%("PASS — the sound net fires on the known positives; its negatives are meaningful."
      if CAL_OK else "FAIL — DO NOT TRUST ANY NEGATIVE BELOW."))

# ======================================================= LIVE RE-RUN AT HEAD
print()
print("="*80)
print("LIVE RE-RUN — sound net, MULTI-LINE, over the whole tracked worktree at HEAD")
print("="*80)
files=tracked()
print("  corpus: %d tracked files (whole repo, not just .softhouse/)"%len(files))
res=collections.defaultdict(list); skipped=0
for f in files:
    if f.startswith(SELF): continue
    txt=read(f)
    if txt is None: skipped+=1; continue
    r=scan_text(txt,SOUND_NET)
    for t,v in r.items():
        for l,x in v: res[t].append((f,l,x))
print("  skipped (binary or >4MB): %d"%skipped)
print()
for t,_ in SOUND_NET:
    v=res.get(t,[])
    print("  %-12s hits=%-6d files=%d"%(t,len(v),len(set(f for f,_,_ in v))))
json.dump({t:res.get(t,[]) for t,_ in SOUND_NET}, open(SELF+"evidence/sound-sweep-HEAD.json","w"), indent=1)

print()
print("  --- S5 (records ... as not existing) + S6 (no guard for either): the RETRACTED CLAIM, verbatim ---")
for t in ("S5-records","S6-noguard"):
    for f,l,x in res.get(t,[]):
        print("    %-11s %s:%d  %s"%(t,f,l,x[:120]))

print()
print("  --- MULTI-LINE-ONLY hits: matches that SPAN a newline and therefore could NOT be found")
print("      by ANY line-oriented sweep in this chain (T224, T227, T232, A2-31/32/33) ---")
ml=[(t,f,l,x) for t,_ in SOUND_NET for f,l,x in res.get(t,[]) if "\\n" in x]
print("      count: %d  (in %d files)"%(len(ml), len(set(f for _,f,_,_ in ml))))
byf=collections.Counter(f for _,f,_,_ in ml)
for f,c in byf.most_common(25): print("      %-88s %d"%(f,c))
json.dump([{"term":t,"file":f,"line":l,"text":x} for t,f,l,x in ml],
          open(SELF+"evidence/multiline-only-hits.json","w"), indent=1)
