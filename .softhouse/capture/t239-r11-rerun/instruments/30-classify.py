#!/usr/bin/env python3
"""T239 — classify every hit the sound instrument surfaced that the original never saw,
and then answer the question the check was ACTUALLY asking.

Classes:
  VIOLATION     a baseline resolved from the moving ref `main` (P-24's exact trap)
  COMPLIANT     a literal sha/blob baseline, with `main` only in an attached comment
  PROSE         `main` inside a comment or an echo label — documentation, not a ref
  JVM-LOG       `main` as the Spring Boot thread name in a captured JVM transcript.
                A word-boundary match, so not a false positive of the REGEX — but a false
                positive of the CHECK: it is not a git ref and never could be.
  OTHER         anything the rules below do not cover — reported, never silently dropped.

Also runs the check's real predicate independently of the regex: does any file in the
population invoke git in a way that RESOLVES `main` as a revision?
"""
import subprocess, sys, os, re, json

REPO = sys.argv[1]
T115 = "bd59187cf83c7c7161db23668e91d45bd46be2a8"
PATHS = [".softhouse/capture/t91/",
         ".softhouse/capture/charges/bin/preconditions.sh",
         ".softhouse/capture/audit-t44/charges/bin/preconditions-COPY.sh"]
os.chdir(REPO)

def git(*a):
    return subprocess.run(["git"] + list(a), capture_output=True, text=True).stdout

hits_path = ".softhouse/capture/t239-r11-rerun/evidence/delta-unseen.txt"
raw = [l for l in open(hits_path).read().split("\n") if l.strip()]
print("hits to classify (the delta the original NEVER SAW): %d" % len(raw))
print("source: %s" % hits_path)
print()

WORD = re.compile(r"\bmain\b")
rows = []
for line in raw:
    body = line[len(T115) + 1:] if line.startswith(T115 + ":") else line
    m = re.match(r"^(.*?):(\d+):(.*)$", body)
    if not m:
        rows.append(("UNPARSED", body, "", ""))
        continue
    f, n, text = m.group(1), int(m.group(2)), m.group(3)
    s = text.strip()
    # the matched token in context
    mm = WORD.search(text)
    ctx = text[max(0, mm.start() - 22):mm.end() + 22] if mm else ""

    if re.search(r"---\s*\[\s*main\s*\]|\[\s*main\s*\]\s", text) or "INFO 1  [" in text:
        cls = "JVM-LOG"
    elif re.search(r"(rev-parse|merge-base|rev-list|show|archive|cat-file|diff|log|ls-tree)\s+[^#]*\bmain\b", text) \
            and not s.startswith("#"):
        cls = "VIOLATION"
    elif re.search(r"^[A-Z_]+=[0-9a-f]{7,40}", s):
        cls = "COMPLIANT"
    elif s.startswith("#") or s.startswith("echo ") or s.startswith('echo"'):
        cls = "PROSE"
    else:
        cls = "OTHER"
    rows.append((cls, f, n, ctx.strip()))

from collections import Counter
counts = Counter(r[0] for r in rows)
print("=" * 78)
print("CLASSIFICATION OF ALL %d PREVIOUSLY-UNSEEN HITS" % len(rows))
print("=" * 78)
for k in ["VIOLATION", "COMPLIANT", "PROSE", "JVM-LOG", "OTHER", "UNPARSED"]:
    if counts.get(k):
        print("  %-10s %3d" % (k, counts[k]))
print("  %-10s %3d   <- must equal the delta above (P-40: count what you skipped)" % ("TOTAL", len(rows)))
print()
for k in ["VIOLATION", "COMPLIANT", "OTHER", "UNPARSED", "PROSE", "JVM-LOG"]:
    sel = [r for r in rows if r[0] == k]
    if not sel:
        continue
    print("--- %s (%d) ---" % (k, len(sel)))
    if k == "JVM-LOG":
        byfile = Counter(r[1] for r in sel)
        print("    %d captured JVM transcripts, all the same Spring Boot startup line," % len(byfile))
        print("    thread name 'main'. Sample context: %r" % sel[0][3])
        for f, c in sorted(byfile.items())[:4]:
            print("      %s  x%d" % (f, c))
        print("      ... %d files total, full list in evidence/classified.json" % len(byfile))
    else:
        for r in sel:
            print("    %s:%s" % (r[1], r[2]))
            print("        %r" % r[3])
    print()

json.dump([{"class": r[0], "file": r[1], "line": r[2], "context": r[3]} for r in rows],
          open(".softhouse/capture/t239-r11-rerun/evidence/classified.json", "w"), indent=1)

print("=" * 78)
print("THE CHECK'S REAL PREDICATE, evaluated WITHOUT the regex")
print("=" * 78)
print("r11 §2 asks: 'every baseline in T115's scripts must be a LITERAL sha'.")
print("So the decisive question is not 'does the word main appear' but 'does any script")
print("RESOLVE a git revision from main'. Evaluated over every .sh in the population:")
print()
files = [f for f in git("ls-tree", "-r", "--name-only", T115, "--", *PATHS).split("\n") if f.endswith(".sh")]
print("  .sh files in population: %d" % len(files))
GITCMD = re.compile(r"git\s+(?:-\S+\s+)*(rev-parse|merge-base|rev-list|show|archive|cat-file|ls-tree|diff|log)\b([^\n]*)")
viol = 0
refs_seen = Counter()
for f in files:
    src = git("show", "%s:%s" % (T115, f))
    for lineno, line in enumerate(src.split("\n"), 1):
        code = line.split("#", 1)[0]
        for g in GITCMD.finditer(code):
            args = g.group(2)
            refs_seen[g.group(1)] += 1
            if re.search(r"\bmain\b|\borigin/main\b|\bHEAD\b", args):
                print("  *** RESOLVES A MOVING REF: %s:%d  %s" % (f, lineno, line.strip()[:120]))
                viol += 1
print("  git revision-resolving invocations found : %d" % sum(refs_seen.values()))
print("  of those, resolving main/origin/main/HEAD: %d" % viol)
print("  breakdown by subcommand: %s" % dict(refs_seen))
print()
print("VERDICT ON THE CHECK ITSELF: %s" % ("VIOLATIONS PRESENT" if viol else
      "no baseline in the population is computed from a moving ref — the check's CONCLUSION was correct"))
