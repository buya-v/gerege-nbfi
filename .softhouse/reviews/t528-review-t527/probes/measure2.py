#!/usr/bin/env python3
"""T528 -- cost of the SMALL form of the classifier fix.

Not "bind every sha to a branch" (that costs 71 of 73 waivers -- unaffordable).
Instead, a DOMINANT REFERENCE VETO plus two anchor demotions:

  V   a sha whose preceding ~40 chars contain a BASE-CITATION word
      (merge base / based on / branched from / forked / diverges / rebased onto /
       ahead of / behind / from) is REFERENCE no matter which anchor caught it
  V2  a sha whose preceding ~40 chars name a DIFFERENT task id is REFERENCE
      (a note citing another task's landing proves nothing about this one)
  D1  `commit <sha>` demoted LANDING -> REFERENCE
  D2  the `stack ...` REGION demoted LANDING -> REFERENCE
  D3  `<branch> (<sha>)` proves LANDING only when <branch> is one THIS task claims

Measured against the real record: how many of the 73 legitimate PRUNED-PROVED
waivers survive?"""
import json, os, sys, glob, importlib.util, re

REPO = sys.argv[1]
spec = importlib.util.spec_from_file_location(
    "cb", os.path.join(REPO, ".softhouse", "bin", "check-branch-published.py"))
cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
res = json.load(open('/tmp/claude-0/-home-user/871c1a31-81ad-5dca-b34a-be2993091ecc'
                     '/scratchpad/real.json'))
proved = {}
for w in res["waived"]:
    if w["kind"] == "PRUNED-PROVED":
        proved.setdefault(w["task"], []).append(w["branch"])
recs = {}
for p in [os.path.join(REPO, ".softhouse", "tasks.json")] + sorted(
        glob.glob(os.path.join(REPO, ".softhouse", "runs", "*.tasks.json"))):
    try:
        d = json.load(open(p))
    except Exception:
        continue
    for t in (d.get("tasks") if isinstance(d, dict) else d) or []:
        if isinstance(t, dict) and t.get("id"):
            recs.setdefault(str(t["id"]), []).append(t)

HEX = cb.HEX
BASE_WORDS = re.compile(
    r"(merge[ -]base|based?\s+on|branch(?:ed)?\s+from|fork(?:ed)?|diverge[sd]?|"
    r"rebased?\s+onto|ahead\s+of|behind|hiding|head)[^.\n]{0,40}$", re.I)
OTHER_TASK = re.compile(r"\b(T\d+|A2-\d+)\b[^.\n]{0,40}$")
LANDING_KEEP = [
    re.compile(r"\blanded\s+(?P<sha>" + HEX + r")\b", re.I),
    re.compile(r"\bmerged?\s+(?:as|at|commit)\s+(?P<sha>" + HEX + r")\b", re.I),
    re.compile(r"\btip\s+(?:is\s+)?(?P<sha>" + HEX + r")\b", re.I),
    re.compile(r"\b(?:COMPLETE|DONE|MERGED|landed)\s*@\s*(?P<sha>" + HEX + r")\b", re.I),
]
BRANCH_PAREN = re.compile(
    r"(?P<br>softhouse/[A-Za-z0-9._+-]+)\s*\(\s*(?P<sha>" + HEX + r")\s*\)")


def landing_shas(t, tid):
    note = cb._note_text(t)
    out = set()
    for f in cb.COMMIT_FIELDS:                       # explicit fields still bind
        v = t.get(f)
        if isinstance(v, str) and v.strip():
            m = cb.HEX_TOKEN.search(v.strip())
            if m:
                out.add(m.group(1))
    own = set(cb.extract_claims(t)[0])
    cands = []
    for rx in LANDING_KEEP:
        for m in rx.finditer(note):
            cands.append((m.group("sha"), m.start("sha")))
    for m in BRANCH_PAREN.finditer(note):
        if cb._clean_branch(m.group("br")) in own:
            cands.append((m.group("sha"), m.start("sha")))
    for sha, at in cands:
        before = note[max(0, at - 60):at]
        if BASE_WORDS.search(before):
            continue
        m = OTHER_TASK.search(before)
        if m and m.group(1) != tid:
            continue
        if cb.DIGEST_CONTEXT.search(before):
            continue
        out.add(sha)
    return out


import subprocess
main_sha = res["origin_main"]
cache = {}


def anc(sha):
    if sha not in cache:
        p = subprocess.run(["git", "-C", REPO, "merge-base", "--is-ancestor",
                            sha, main_sha], capture_output=True)
        cache[sha] = p.returncode == 0
    return cache[sha]


survive, lost = [], []
for tid, brs in proved.items():
    ok = False
    for t in recs.get(tid, []):
        for sha in landing_shas(t, tid):
            try:
                if anc(sha):
                    ok = True
            except Exception:
                pass
    for b in brs:
        (survive if ok else lost).append((tid, b))

print("PRUNED-PROVED waivers today          : %d" % sum(len(v) for v in proved.values()))
print("survive the SMALL fix                : %d" % len(survive))
print("would newly become findings          : %d" % len(lost))
for tid, b in lost:
    print("   %-8s %s" % (tid, b))
