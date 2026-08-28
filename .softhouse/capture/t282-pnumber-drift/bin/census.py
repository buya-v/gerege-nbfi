#!/usr/bin/env python3
"""T282 CENSUS -- enumerate every P-number citation in the repository.

Data-only. Makes no repair and no judgement about which register is
authoritative; that argument is in the T282 handoff. Writes out/census.json
and out/census.txt.

The search scope is printed in the output so a reader can tell what the sweep
could NOT have found. P-66 / P-70 (patterns.md): "Latent", "not promoted",
"can never resolve", "no guard exists" -- four ways this program stated a
SEARCH RESULT as a WORLD FACT. "Not found" is a statement about the search.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# Anchored to this file, never to the caller's cwd. T165 / T201: FindRepoRoot(".")
# made the conformance binary resolve its repo from the CALLER's cwd, and that
# decided a frozen-contract digest gate. P-56: a guard's scope defect is
# invisible in every tree except the one it will run in.
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
PATTERNS = os.path.join(ROOT, ".softhouse", "patterns.md")
GATES = os.path.join(ROOT, ".softhouse", "gates-proposed-answers.md")

# A pattern-id citation. Leading zeros are excluded ON PURPOSE: `P-00`, `P-02`,
# `P-02b` are GOLDEN VECTOR ids in this repo -- a different namespace entirely.
CITE = re.compile(r'(?<![A-Za-z0-9_])P-([1-9][0-9]*)(?![0-9])')

# A definition line in patterns.md: heading, bold run, or list bullet whose FIRST
# token is the id, followed by a separator and the rule sentence.
# Kept BYTE-IDENTICAL to the two regexes in check-pnumber-citations.py on
# purpose: a census that counts definitions differently from the checker that
# grades them is the same defect one layer out. An id-only bold run
# (`**P-40** - text`) is a RESTATEMENT, not a definition, and is excluded.
DEFN_HEAD = re.compile(r'^#{2,4}\s+P-([1-9][0-9]*)\s*[.·—–-]\s+(.+)$')
DEFN_BOLD = re.compile(r'^(?:[-*>]\s+)?\*\*P-([1-9][0-9]*)\s*[.·—–-]\s+(.+)$')
DEFN_GATES = re.compile(r'^#{2,4}\s+P-([1-9][0-9]*)\s*[.·—–-]\s+(.*)$')


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read().split("\n")


def build_register(path, rxs):
    """Every definition site in file order. First occurrence wins; later ones are
    recorded as COLLISIONS rather than silently dropped."""
    reg = {}
    collisions = []
    for i, raw in enumerate(read(path), 1):
        m = None
        for rx in rxs:
            m = rx.match(raw.strip())
            if m:
                break
        if not m:
            continue
        n = int(m.group(1))
        entry = {"id": n, "line": i, "title": m.group(2).strip().strip("*").strip()}
        if n in reg:
            collisions.append({"id": n, "first": reg[n], "again": entry})
        else:
            reg[n] = entry
    return reg, collisions


def tracked_files():
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT,
                         capture_output=True, check=True).stdout
    return [f for f in out.decode("utf-8", "replace").split("\0") if f]


def main():
    reg, collisions = build_register(PATTERNS, (DEFN_HEAD, DEFN_BOLD))
    greg, gcollisions = build_register(GATES, (DEFN_GATES,))

    defined = sorted(reg)
    gaps = [n for n in range(1, (max(defined) if defined else 0) + 1) if n not in reg]

    prel = os.path.relpath(PATTERNS, ROOT)
    grel = os.path.relpath(GATES, ROOT)
    defn_lines = set((prel, e["line"]) for e in reg.values())
    defn_lines |= set((prel, c["again"]["line"]) for c in collisions)
    defn_lines |= set((grel, e["line"]) for e in greg.values())

    files = tracked_files()
    sites = []
    skipped = []
    for rel in files:
        ap = os.path.join(ROOT, rel)
        if not os.path.isfile(ap):
            continue
        try:
            with open(ap, "rb") as fh:
                head = fh.read(8192)
            if b"\0" in head:
                skipped.append(rel + " (binary: NUL in first 8192 bytes)")
                continue
            lines = read(ap)
        except OSError as exc:
            # Never swallow. P-40: an enumerator with a bare `except: continue`
            # is a silent-skip guard.
            skipped.append("%s (UNREADABLE: %s)" % (rel, exc))
            continue
        for i, raw in enumerate(lines, 1):
            for m in CITE.finditer(raw):
                sites.append({
                    "file": rel,
                    "line": i,
                    "id": int(m.group(1)),
                    "col": m.start() + 1,
                    "is_definition": (rel, i) in defn_lines,
                    "text": raw.strip()[:400],
                })

    dangling = sorted(set(s["id"] for s in sites if s["id"] not in reg))
    by_id = {}
    by_file = {}
    for s in sites:
        by_id.setdefault(s["id"], []).append(s)
        by_file[s["file"]] = by_file.get(s["file"], 0) + 1

    census = {
        "root": ROOT,
        "scope": {
            "enumerated": "every file reported by `git ls-files` at the repo root",
            "files_listed": len(files),
            "not_read": [
                "untracked and gitignored files -- nothing outside `git ls-files` was opened",
                "files whose first 8192 bytes contain NUL (see skipped)",
                "the pinned Fineract checkout at /Users/buv/fineract -- a separate tree",
                "GIT COMMIT MESSAGES -- they are not files; this census does NOT cover them",
                "zero-padded ids P-00/P-01/P-02/P-02b -- golden VECTOR ids, other namespace",
            ],
        },
        "register_patterns_md": reg,
        "register_patterns_md_collisions": collisions,
        "register_gates_proposed_answers_md": greg,
        "register_gates_collisions": gcollisions,
        "register_gaps": gaps,
        "dangling_ids_cited_but_undefined": dangling,
        "cross_file_collisions": sorted(set(reg) & set(greg)),
        "totals": {
            "sites": len(sites),
            "definition_sites": sum(1 for s in sites if s["is_definition"]),
            "citation_sites": sum(1 for s in sites if not s["is_definition"]),
            "distinct_ids_cited": len(by_id),
            "distinct_files": len(by_file),
        },
        "sites_per_file": dict(sorted(by_file.items(), key=lambda kv: -kv[1])),
        "sites_per_id": dict((str(k), len(v)) for k, v in sorted(by_id.items())),
        "skipped": skipped,
        "sites": sites,
    }

    outdir = os.path.abspath(os.path.join(HERE, "..", "out"))
    with open(os.path.join(outdir, "census.json"), "w", encoding="utf-8") as fh:
        json.dump(census, fh, indent=1, ensure_ascii=False)

    with open(os.path.join(outdir, "census.txt"), "w", encoding="utf-8") as fh:
        w = fh.write
        w("T282 P-NUMBER CENSUS\n====================\n\n")
        w("SCOPE -- what was read, and what this sweep could NOT have found:\n")
        w("  READ: %s (%d files)\n" % (census["scope"]["enumerated"], len(files)))
        for x in census["scope"]["not_read"]:
            w("  NOT READ: %s\n" % x)
        w("\nREGISTER .softhouse/patterns.md: %d ids, gaps %s\n" % (len(reg), gaps or "NONE"))
        w("REGISTER .softhouse/gates-proposed-answers.md: %d ids -> %s\n" % (len(greg), sorted(greg)))
        w("\nIN-FILE COLLISIONS in patterns.md (one id, two different rules): %d\n" % len(collisions))
        for c in collisions:
            w("  P-%-3d :%-5d %s\n" % (c["id"], c["first"]["line"], c["first"]["title"][:92]))
            w("        :%-5d %s\n" % (c["again"]["line"], c["again"]["title"][:92]))
        w("\nCROSS-FILE COLLISIONS (an id defined in BOTH registers): %s\n"
          % census["cross_file_collisions"])
        w("\nDANGLING ids cited but defined nowhere: %s\n" % (dangling or "NONE"))
        w("\nTOTALS: %s\n" % json.dumps(census["totals"]))
        w("\nSITES PER FILE (%d files):\n" % len(by_file))
        for f, n in census["sites_per_file"].items():
            w("  %5d  %s\n" % (n, f))
        w("\nSITES PER ID:\n")
        for k, v in census["sites_per_id"].items():
            w("  P-%-4s %d\n" % (k, v))
        w("\nEVERY SITE  file:line:id  text\n")
        for s in sites:
            w("%s:%d:P-%d%s  %s\n"
              % (s["file"], s["line"], s["id"], " [DEFN]" if s["is_definition"] else "", s["text"]))

    print("census: %d sites in %d files; register %d ids, gaps %s; "
          "in-file collisions %d; cross-file collisions %s; dangling %s"
          % (len(sites), len(by_file), len(reg), gaps or "none", len(collisions),
             census["cross_file_collisions"], dangling or "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
