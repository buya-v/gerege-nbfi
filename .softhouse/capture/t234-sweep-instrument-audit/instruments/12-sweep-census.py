#!/usr/bin/env python3
"""
T234 — FOCUSED CENSUS: SWEEP INSTRUMENTS ONLY.

11-census.py found 4,508 search-engine invocation sites under .softhouse/.  Most are
capture plumbing (pull a field out of a JSON dump).  Those are NOT sweep instruments and
auditing them is not this task.  This census applies an explicit, stated predicate.

DEFINITION USED (stated so it is checkable, and so what it EXCLUDES is visible):
  A SWEEP INSTRUMENT is a committed artefact whose purpose is to enumerate a population
  of claims/occurrences ACROSS THE REPOSITORY in support of a closure statement
  ("the population is closed", "no other site exists", "every hit was opened").

OPERATIONALISED as EITHER:
  D1  basename matches sweep|census|scan|enumerat|survey|leakgrep|misscheck|missprobe
  D2  file contains a REPO-WIDE search: `git grep` / `grep -r` / `git ls-files` iteration
  D3  file contains a CLOSURE CLAIM (the sentence a sweep exists to license)

  script instrument  = (D1 or D2) and the file is .sh/.py   -> AUDITABLE, re-runnable
  prose-only sweep   = D3 in a .md with no committed instrument -> UNAUDITABLE BY
                       CONSTRUCTION.  That is itself the finding.
"""
import re, os, subprocess, json, collections

ROOT = subprocess.run(["git","rev-parse","--show-toplevel"],capture_output=True,text=True).stdout.strip()
os.chdir(ROOT)
SELF = ".softhouse/capture/t234-sweep-instrument-audit/"
files = [f for f in subprocess.run(["git","ls-files","--",".softhouse"],
         capture_output=True,text=True).stdout.split("\n") if f and not f.startswith(SELF)]

D1 = re.compile(r'(sweep|census|scan|enumerat|survey|leakgrep|misscheck|missprobe)', re.I)
D2 = re.compile(r'(git\s+grep|grep\s+-[a-zA-Z]*[rR]\b|git\s+ls-files)')
D3 = re.compile(
  r'(population is closed|no (other|further|fourth|fifth|second|third) (surviving |live |remaining )?'
  r'(site|instance|occurrence|assertion|restatement|copy|hit|survivor)'
  r'|does not exist anywhere|exists? (anywhere )?in (this|the) repos'
  r'|every hit was opened|I opened every|swept the (whole|entire)'
  r'|whole[- ]repo sweep|repo-wide sweep|whole repository for'
  r'|the sweep (above|below|found|returned)|terms swept|patterns swept'
  r'|closed the population)', re.I)

ENGINE_DEP = re.compile(r'\\(b|B|d|D|s|S|w|W|<|>|A|Z|z|K|h|v|R|N|p\{)')

rows=[]
for f in files:
    base=os.path.basename(f); ext=os.path.splitext(f)[1]
    if ext not in (".sh",".py",".md",".json",".txt"): continue
    try: txt=open(f,encoding="utf-8",errors="replace").read()
    except Exception: continue
    if len(txt)>4_000_000: continue
    d1=bool(D1.search(base)); d2=bool(D2.search(txt))
    d3=[(i,l.strip()[:190]) for i,l in enumerate(txt.splitlines(),1) if D3.search(l)]
    kind = "script" if ext in (".sh",".py") else "prose"
    if kind=="script":
        if not (d1 or (d2 and d3)): continue
    else:
        if not d3: continue
    engines=collections.Counter(); voids=[]; deadcd=None
    if kind=="script":
        for i,l in enumerate(txt.splitlines(),1):
            for m in re.finditer(r'(git\s+grep|(?<![-\w./])e?grep\b|\bre\.(?:search|match|findall|finditer|compile)\()', l):
                tail=l[m.end():m.end()+300]
                fl="".join(re.findall(r'(?<=[ \t])-([a-zA-Z]+)',tail))
                q=re.search(r"""r?'((?:[^'\\]|\\.)*)'|r?"((?:[^"\\]|\\.)*)\"""",tail)
                pat=(q.group(1) if q and q.group(1) is not None else (q.group(2) if q else None))
                tok=m.group(1)
                if tok.startswith("git"):
                    eng="git grep -P" if "P" in fl else ("git grep -F" if "F" in fl else ("git grep -E" if "E" in fl else "git grep BRE"))
                elif tok.startswith("re."): eng="python re"
                else: eng=("grep -P (NONEXISTENT on BSD)" if "P" in fl else ("grep -E" if "E" in fl else "grep BRE"))
                engines[eng]+=1
                if pat and ENGINE_DEP.search(pat) and eng in ("git grep -E","git grep BRE","grep -P (NONEXISTENT on BSD)"):
                    voids.append((i,eng,pat[:120]))
        cd=re.search(r'cd\s+"?(/Users/buv/gerege-nbfi/\.claude/worktrees/[A-Za-z0-9_-]+)',txt)
        if not cd:
            cd=re.search(r'=\s*"?(/Users/buv/gerege-nbfi/\.claude/worktrees/[A-Za-z0-9_-]+)',txt)
        if cd: deadcd=(cd.group(1), os.path.isdir(cd.group(1)))
    rows.append(dict(file=f,kind=kind,d1=d1,d2=d2,d3=len(d3),d3_sample=d3[:3],
                     engines=dict(engines),voids=voids,deadcd=deadcd))

json.dump(rows,open(SELF+"evidence/sweep-census.json","w"),indent=1)
scripts=[r for r in rows if r["kind"]=="script"]
prose  =[r for r in rows if r["kind"]=="prose"]
print("SWEEP-INSTRUMENT CENSUS  (corpus: %d tracked files under .softhouse/, this dir excluded)"%len(files))
print("  matched the sweep predicate : %d   (script instruments %d, prose-only %d)"%(len(rows),len(scripts),len(prose)))
print()
print("### SCRIPT INSTRUMENTS — engine + verdict")
for r in sorted(scripts,key=lambda x:x["file"]):
    engs=", ".join("%s x%d"%(k,v) for k,v in sorted(r["engines"].items()))
    verdict=[]
    if r["voids"]: verdict.append("PARTIALLY-VOID-ESCAPE(%d)"%len(r["voids"]))
    if r["deadcd"] and not r["deadcd"][1]: verdict.append("UNREPRODUCIBLE-DEAD-CD")
    if "grep -P (NONEXISTENT on BSD)" in r["engines"]: verdict.append("VOID-NOOPTION")
    if not verdict: verdict=["SOUND-on-escapes"]
    print("  %s"%r["file"])
    print("      engines : %s"%(engs or "(none parsed)"))
    print("      verdict : %s"%(" + ".join(verdict)))
    if r["deadcd"]: print("      hard path: .../%s  exists=%s"%(r["deadcd"][0].split('/')[-1], r["deadcd"][1]))
    for v in r["voids"]: print("      VOID    : line %d  %s  pattern=%r"%v)
print()
print("### PROSE-ONLY SWEEPS — a closure claim in a .md with no committed instrument")
print("###   UNAUDITABLE BY CONSTRUCTION: the commands were never recorded.")
for r in sorted(prose,key=lambda x:-x["d3"]):
    print("  %-92s closure-claim lines: %d"%(r["file"],r["d3"]))
    for i,l in r["d3_sample"]: print("        :%d  %s"%(i,l[:150]))
