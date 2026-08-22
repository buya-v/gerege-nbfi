#!/usr/bin/env python3
"""
T234 — SWEEP INSTRUMENT CENSUS (fast rewrite of 10-census.py; the first version
scanned every tracked byte and was killed at >4min on the 1.3M-line capture dumps).

Two INDEPENDENT enumeration programs (P-58), NAMED, over the same corpus, reconciled.
CORPUS: every file tracked by git under .softhouse/ at this worktree's HEAD.

PROGRAM A — INVOCATION-SITE.  git grep -l pre-filters to files that contain a
  search-engine token at all; those files are then parsed line by line.  Engine is
  derived from the invocation's own flags, NOT from the author's prose.

PROGRAM B — SELF-DECLARATION.  Files that CALL THEMSELVES a sweep/census/enumeration
  by filename, or whose text asserts a swept population.  Catches PROSE-ONLY sweeps:
  a sweep recorded in a .md with no committed script behind it.

MEASURED engine readings (transcripts/01,02 in this directory):
  git grep -E        : \\b \\d \\s \\w ALL read as the LITERAL letter. VOID for escapes.
  git grep -P        : PCRE2 -- all real.  SOUND.
  /usr/bin/grep -E   : BSD grep 2.6.0-FreeBSD -- \\b \\d \\s \\w ALL REAL. SOUND.
                       (this is what a .sh script gets; ugrep is NOT exported into scripts)
  /usr/bin/grep -P   : DOES NOT EXIST. exit 2, empty output, indistinguishable from "no match".
  ugrep 7.5.0        : ONLY reachable from the agent's interactive shell function wrapper.
"""
import json, os, re, subprocess, collections

ROOT = subprocess.run(["git","rev-parse","--show-toplevel"],capture_output=True,text=True).stdout.strip()
os.chdir(ROOT)
SELF = ".softhouse/capture/t234-sweep-instrument-audit/"

def gitgrep_l(pat, *paths):
    r = subprocess.run(["git","grep","-l","-I","-E",pat,"--"]+list(paths),
                       capture_output=True,text=True)
    return [x for x in r.stdout.split("\n") if x]

all_files = [f for f in subprocess.run(["git","ls-files","--",".softhouse"],
             capture_output=True,text=True).stdout.split("\n") if f]

# ---------- PROGRAM A ----------
cand = set()
for p in [r'git[ \t]+grep', r'(^|[^-a-zA-Z_./])e?grep[ \t]', r'\bugrep\b', r're\.(search|match|findall|finditer|compile|sub|fullmatch)\(']:
    cand |= set(gitgrep_l(p, ".softhouse"))
cand = sorted(f for f in cand if not f.startswith(SELF))

ENGINE_DEP = re.compile(r'\\(b|B|d|D|s|S|w|W|<|>|A|Z|z|h|H|v|V|R|K|N|p\{)')
INVOKE = re.compile(r'''(?x)
   (?P<git>\bgit\s+grep\b)
 | (?P<ug>\bugrep\b)
 | (?P<eg>\begrep\b)
 | (?P<gr>(?<![-\w./])grep\b)
 | (?P<py>\bre\.(?:search|match|findall|finditer|sub|compile|fullmatch)\()
''')
QUOTED = re.compile(r"""r?'((?:[^'\\]|\\.)*)'|r?"((?:[^"\\]|\\.)*)\"""")

def pattern_after(line, pos):
    m = QUOTED.search(line, pos)
    if not m: return None
    g = m.group(1) if m.group(1) is not None else m.group(2)
    # skip a pure flag-looking or path-looking capture
    return g

def engine_for(kind, line, pos):
    tail = line[pos:pos+300]
    fl = "".join(re.findall(r'(?<=[ \t])-([a-zA-Z]+)', tail))
    if kind == "git":
        if "P" in fl: return "git grep -P (PCRE2)", "SOUND", fl
        if "F" in fl: return "git grep -F (fixed strings)", "SOUND-literal", fl
        if "E" in fl: return "git grep -E (git ERE)", "ESCAPES-VOID", fl
        return "git grep (git BRE, default)", "ESCAPES-VOID", fl
    if kind in ("gr","eg"):
        if "P" in fl: return "grep -P via /usr/bin/grep => NONEXISTENT OPTION", "NONEXISTENT", fl
        if "E" in fl or kind=="eg": return "BSD grep -E (script) / ugrep -E (interactive)", "SOUND", fl
        return "BSD grep BRE (script) / ugrep BRE (interactive)", "BRE", fl
    if kind == "ug": return "ugrep (explicit)", "SOUND", ""
    return "python re", "SOUND", ""

sites = []
for f in cand:
    try: txt = open(f, encoding="utf-8", errors="replace").read()
    except Exception: continue
    if len(txt) > 8_000_000: continue
    for i, line in enumerate(txt.splitlines(), 1):
        if len(line) > 4000: continue
        for m in INVOKE.finditer(line):
            kind = m.lastgroup
            pat = pattern_after(line, m.end())
            eng, cls, fl = engine_for(kind, line, m.end())
            esc = sorted(set(ENGINE_DEP.findall(pat))) if pat else []
            sites.append(dict(file=f, line=i, kind=kind, engine=eng, cls=cls,
                              flags=fl, pattern=pat, escapes=esc, src=line.strip()[:230]))

# ---------- PROGRAM B ----------
NAME_DECL = re.compile(r'(sweep|census|scan|enumerat|survey|inventor|leakgrep|probe-sweep)', re.I)
CLAIM = re.compile(r'(population is closed|no other (surviving |live )?(site|instance|occurrence|assertion|restatement)'
                   r'|does not exist (anywhere|in this repos)|no (fourth|fifth|further|other) surviving'
                   r'|swept the (whole |entire )?repos|repo-wide sweep|whole-repo sweep|the sweep (above|below)'
                   r'|I swept|terms swept|patterns swept|sweep for the claim)', re.I)
selfdecl = {}
for f in all_files:
    if f.startswith(SELF): continue
    nm = bool(NAME_DECL.search(os.path.basename(f)))
    hits = []
    if f.endswith((".md",".sh",".py",".json",".txt")):
        try: txt = open(f, encoding="utf-8", errors="replace").read()
        except Exception: txt = ""
        if len(txt) < 4_000_000:
            for i,l in enumerate(txt.splitlines(),1):
                if CLAIM.search(l): hits.append((i,l.strip()[:200]))
    if nm or hits:
        selfdecl[f] = dict(name_declares=nm, claim_lines=len(hits), sample=hits[:4])

A = collections.OrderedDict()
for s in sites: A.setdefault(s["file"], []).append(s)

json.dump(dict(sites=sites, selfdecl=selfdecl,
               corpus=len(all_files), progA_files=len(A), progB_files=len(selfdecl)),
          open(SELF+"evidence/census.json","w"), indent=1)

print("CORPUS  git-tracked files under .softhouse/ :", len(all_files))
print("PROGRAM A  candidate files (git grep -l prefilter):", len(cand))
print("PROGRAM A  invocation sites :", len(sites), "across", len(A), "files")
print("PROGRAM B  self-declaring files :", len(selfdecl))
onlyA = sorted(set(A)-set(selfdecl)); onlyB = sorted(set(selfdecl)-set(A))
print("  A-only:", len(onlyA), "  B-only:", len(onlyB), "  both:", len(set(A)&set(selfdecl)))
print()
print("=== ENGINE CLASS across all", len(sites), "invocation sites ===")
for k,v in collections.Counter(s["cls"] for s in sites).most_common(): print("  %-16s %d" % (k,v))
print()
print("=== ENGINE across all invocation sites ===")
for k,v in collections.Counter(s["engine"] for s in sites).most_common(): print("  %-58s %d" % (k,v))
print()
bad = [s for s in sites if s["escapes"]]
print("=== SITES CARRYING AN ENGINE-DEPENDENT ESCAPE:", len(bad), "===")
for k,v in collections.Counter(s["engine"] for s in bad).most_common(): print("  %-58s %d" % (k,v))
print()
VOID = [s for s in bad if s["cls"] in ("ESCAPES-VOID",)]
print("=== *** VOID *** : engine-dependent escape UNDER git grep -E/BRE :", len(VOID), "===")
for s in VOID:
    print("  %s:%s" % (s["file"], s["line"]))
    print("      engine=%s  escapes=%s" % (s["engine"], s["escapes"]))
    print("      pattern=%r" % (s["pattern"],))
print()
NX = [s for s in sites if s["cls"]=="NONEXISTENT"]
print("=== *** VOID BY NONEXISTENT OPTION *** : grep -P in a script :", len(NX), "===")
for s in NX: print("  %s:%s  %s" % (s["file"], s["line"], s["src"][:150]))
print()
print("=== PROGRAM B files that PROGRAM A found NO invocation in (PROSE-ONLY sweep candidates) ===")
print("  count:", len(onlyB))
for f in onlyB:
    d = selfdecl[f]
    if d["claim_lines"]:
        print("  %-96s claimlines=%d" % (f, d["claim_lines"]))
