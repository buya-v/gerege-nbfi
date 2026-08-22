#!/usr/bin/env python3
"""
T234 — SWEEP INSTRUMENT CENSUS.

Two INDEPENDENT enumeration programs (P-58), named, run over the same corpus,
then reconciled.  The corpus is every file tracked by git under .softhouse/.

PROGRAM A — INVOCATION-SITE.  Find every line that invokes a text-search engine
  (git grep / grep / egrep / rg / ugrep / ack / python re.*).  Engine is derived
  from the invocation, NOT from the author's prose.

PROGRAM B — SELF-DECLARATION.  Find every file that CALLS ITSELF a sweep, census,
  scan, enumeration or survey (filename or content), including .md prose files
  that record a sweep with no script behind it.

Escapes that differ across the four engines reachable from this repo are then
detected per pattern.

Engines and their MEASURED readings (see transcripts/01,02):
  git grep -E   : \\b is a LITERAL 'b'.            \\d \\s \\w also literal.
  git grep -P   : PCRE2. \\b \\d \\s \\w all real.
  /usr/bin/grep -E (BSD 2.6.0-FreeBSD, what a .sh script gets): \\b \\s \\w REAL, \\d literal 'd'.
  /usr/bin/grep -P : DOES NOT EXIST. exit 2, no output, looks like "no matches".
  ugrep 7.5.0   : reachable ONLY from the agent's interactive shell (function wrapper,
                  not exported into scripts). Honours \\b under -E (T232).
"""
import json, os, re, subprocess, sys, collections

ROOT = subprocess.run(["git","rev-parse","--show-toplevel"],capture_output=True,text=True).stdout.strip()
os.chdir(ROOT)

files = subprocess.run(["git","ls-files","--","​.softhouse".replace("\u200b","")],
                       capture_output=True,text=True).stdout.split()
files = [f for f in files if f.startswith(".softhouse/")]

# ---------- escape detection ----------
# escapes whose meaning DIFFERS between at least two of the four engines
ENGINE_DEPENDENT = re.compile(r'\\(b|B|d|D|s|S|w|W|<|>|A|Z|z|h|H|v|V|R|K|p\{|N)')
PCRE_ONLY        = re.compile(r'\(\?[:=!<PimsxU#]|\\K|\\A|\\z|\*\+|\+\+|\{\d+,?\d*\}\+')

# ---------- PROGRAM A : invocation sites ----------
INVOKE = re.compile(r'''(?x)
   (?P<git>\bgit\s+grep\b)
 | (?P<ug>\bugrep\b)
 | (?P<rg>\brg\b(?=\s+-|\s+['"]))
 | (?P<eg>\begrep\b)
 | (?P<gr>(?<![-\w./])grep\b)
 | (?P<py>\bre\.(search|match|findall|finditer|sub|compile|fullmatch)\b)
''')

def extract_pattern(line, pos):
    """best-effort: first quoted string after the invocation token"""
    tail = line[pos:]
    m = re.search(r"""'((?:[^'\\]|\\.)*)'|"((?:[^"\\]|\\.)*)"|r'([^']*)'|r"([^"]*)\"""", tail)
    if not m: return None
    for g in m.groups():
        if g is not None: return g
    return None

def flags_of(line, pos):
    tail = line[pos:pos+400]
    return set(re.findall(r'(?<=\s)-[a-zA-Z]+', tail))

progA = []   # (file, lineno, engine, flags, pattern, escapes)
for f in files:
    try:
        txt = open(f, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    for i, line in enumerate(txt.splitlines(), 1):
        s = line.strip()
        for m in INVOKE.finditer(line):
            kind = m.lastgroup
            # ignore the census's own instruments
            if f.startswith(".softhouse/capture/t234-sweep-instrument-audit/"): continue
            pat = extract_pattern(line, m.end())
            fl  = flags_of(line, m.end())
            flat = "".join(x.lstrip("-") for x in fl)
            if kind == "git":
                eng = "git grep -P (PCRE2)" if "P" in flat else \
                      ("git grep -F (fixed)" if "F" in flat else
                       ("git grep -E (git ERE: \\b == literal b)" if "E" in flat
                        else "git grep (basic, git BRE)"))
            elif kind in ("gr","eg"):
                eng = ("BSD grep -P => DOES NOT EXIST (exit 2)" if "P" in flat else
                       "BSD grep -E" if ("E" in flat or kind=="eg") else "BSD grep (BRE)")
            elif kind == "ug":  eng = "ugrep (explicit)"
            elif kind == "rg":  eng = "ripgrep"
            else:               eng = "python re (sound)"
            esc = sorted(set(ENGINE_DEPENDENT.findall(pat))) if pat else []
            progA.append(dict(file=f, line=i, engine=eng, flags=sorted(fl),
                              pattern=pat, escapes=esc, src=s[:200]))

# ---------- PROGRAM B : self-declaration ----------
NAME_DECL = re.compile(r'(sweep|census|scan|enumerat|survey|inventor|leakgrep|grep)', re.I)
TEXT_DECL = re.compile(r'\b(swept|sweep|sweeps|census|censused|enumerat\w*|scanned the repo\w*|'
                       r'repo-wide|repository-wide|grepp?ed|population is closed|no other (site|instance|occurrence))\b', re.I)
progB = {}
for f in files:
    hit_name = bool(NAME_DECL.search(os.path.basename(f)))
    try:
        txt = open(f, encoding="utf-8", errors="replace").read()
    except Exception:
        txt = ""
    if f.startswith(".softhouse/capture/t234-sweep-instrument-audit/"): continue
    hits = [(i,l.strip()[:220]) for i,l in enumerate(txt.splitlines(),1) if TEXT_DECL.search(l)]
    if hit_name or hits:
        progB[f] = dict(name_declares=hit_name, decl_lines=len(hits), sample=hits[:3])

# ---------- reconcile ----------
A_files = collections.OrderedDict()
for r in progA:
    A_files.setdefault(r["file"], []).append(r)

out = dict(
    corpus_files=len(files),
    programA_invocation_sites=len(progA),
    programA_files=len(A_files),
    programB_files=len(progB),
    in_A_not_B=sorted(set(A_files)-set(progB)),
    in_B_not_A=sorted(set(progB)-set(A_files)),
    both=sorted(set(A_files)&set(progB)),
)
json.dump(dict(summary=out, sites=progA, selfdecl=progB),
          open(".softhouse/capture/t234-sweep-instrument-audit/evidence/census.json","w"),
          indent=1)

print("corpus (git-tracked files under .softhouse/):", len(files))
print("PROGRAM A  invocation sites:", len(progA), "in", len(A_files), "files")
print("PROGRAM B  self-declaring files:", len(progB))
print("  A only:", len(out["in_A_not_B"]), " B only:", len(out["in_B_not_A"]), " both:", len(out["both"]))
print()
print("=== engine distribution across ALL invocation sites ===")
for e,c in collections.Counter(r["engine"] for r in progA).most_common():
    print("  %-46s %d" % (e,c))
print()
print("=== SITES WITH ENGINE-DEPENDENT ESCAPES ===")
bad = [r for r in progA if r["escapes"]]
print("  total:", len(bad))
for e,c in collections.Counter(r["engine"] for r in bad).most_common():
    print("    %-46s %d" % (e,c))
print()
print("=== per-file rollup of escape-bearing sites ===")
byf = collections.Counter(r["file"] for r in bad)
for f,c in byf.most_common():
    engs = sorted(set(r["engine"] for r in bad if r["file"]==f))
    print("  %-92s %2d  %s" % (f, c, "; ".join(engs)))
