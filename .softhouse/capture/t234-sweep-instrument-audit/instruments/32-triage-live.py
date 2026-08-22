#!/usr/bin/env python3
"""
T234 — TRIAGE the multi-line sweep's 743 newline-spanning hits down to LIVE artefacts.

A hit in a frozen handoff / review transcript / captured output is EVIDENCE, not a defect
(T114/T176: a quotation correctly attributed is not a defect, and a frozen transcript is
evidence, not a bug).  What matters is a hit in an artefact a reader treats as CURRENT.

LIVE set, stated explicitly so the scope is checkable:
    docs/adr/**            the ratified ADRs
    .softhouse/conformance.sh, gates.md, patterns.md, RESUME.md, program.json, tasks.json
    .softhouse/guards/**, .softhouse/bin/**, .softhouse/vectors/**
    nexus/**               the Go module
FROZEN (excluded, and counted): .softhouse/handoff/**, .softhouse/reviews/**,
    .softhouse/capture/**, anything *-output.txt / *-evidence/**.
"""
import json, re, os, collections

SELF=".softhouse/capture/t234-sweep-instrument-audit/"
ml=json.load(open(SELF+"evidence/multiline-only-hits.json"))

def live(f):
    if f.startswith("docs/adr/"): return True
    if f.startswith("nexus/"): return True
    if f.startswith(".softhouse/guards/") or f.startswith(".softhouse/bin/") \
       or f.startswith(".softhouse/vectors/"): return True
    return f in (".softhouse/conformance.sh",".softhouse/gates.md",".softhouse/patterns.md",
                 ".softhouse/RESUME.md",".softhouse/program.json",".softhouse/tasks.json",
                 ".softhouse/uat.md",".softhouse/reference-oracle.md",
                 ".softhouse/gates-proposed-answers.md","CLAUDE.md")

L=[h for h in ml if live(h["file"])]
F=[h for h in ml if not live(h["file"])]
print("multi-line-only hits total : %d"%len(ml))
print("  in LIVE artefacts        : %d  (in %d files)"%(len(L),len(set(h['file'] for h in L))))
print("  in FROZEN evidence       : %d  (in %d files) -- NOT triaged individually (P-40)"
      %(len(F),len(set(h['file'] for h in F))))
print()
print("### EVERY multi-line-only hit in a LIVE artefact, file:line, term, matched text")
print("### (a line-oriented sweep -- i.e. every sweep this program has ever run -- CANNOT see these)")
for h in sorted(L,key=lambda x:(x["file"],x["line"])):
    print("  %-52s :%-6d %-11s %s"%(h["file"],h["line"],h["term"],h["text"][:120]))
byf=collections.Counter(h["file"] for h in L)
print()
print("### rollup")
for f,c in byf.most_common(): print("  %-56s %d"%(f,c))
json.dump(L,open(SELF+"evidence/multiline-live-hits.json","w"),indent=1)
