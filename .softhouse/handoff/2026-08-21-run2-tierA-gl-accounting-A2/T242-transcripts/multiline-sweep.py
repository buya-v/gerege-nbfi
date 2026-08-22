import os, re, sys

# MULTI-LINE + MARKUP-TOLERANT sweep, python3 re (sound engine per the driver's
# measured table). Whitespace-insensitive across newlines, and tolerant of
# markdown emphasis characters between words.
pat = re.compile(r"ZERO[\s*_`]+journal[\s*_`]+entries|zero[\s*_`]+receivable[\s*_`]+entries", re.I)
skip = {'.git', 'toolchain', 'gocache', 'gomodcache', 'gopath'}

root_dir = sys.argv[1]
hits = {}
for root, dirs, files in os.walk(root_dir):
    dirs[:] = [d for d in dirs if d not in skip]
    for f in files:
        p = os.path.join(root, f)
        try:
            t = open(p, encoding='utf-8', errors='ignore').read()
        except Exception:
            continue
        n = len(pat.findall(t))
        if n:
            hits[p] = n

# CALIBRATION, published: a known POSITIVE and a known NEGATIVE.
pos = pat.search("gl 18, 22, 16 have ZERO journal\n   entries")
neg = pat.search("ZZQX-T242-string-that-exists-nowhere")
print("CALIBRATION  known positive (split across a newline): %s" % ("MATCHED" if pos else "MISSED -- INSTRUMENT BROKEN"))
print("CALIBRATION  known negative (fabrication check)     : %s" % ("FABRICATED -- INSTRUMENT BROKEN" if neg else "correctly absent"))
print()
print("MULTI-LINE / MARKUP-TOLERANT sweep results:")
for p, n in sorted(hits.items()):
    print("  %2d  %s" % (n, p))

line_found = {
    'capabilities-ledger.json', 'tasks.json', 'REVIEW.md', 'T242-handoff.md',
    'report.go', 'notgraded.go', 'capability.go',
}
print()
print("=== SITES THE LINE-ORIENTED LITERAL SWEEP MISSED ===")
missed = False
for p in sorted(hits):
    base = os.path.basename(p)
    if base in line_found:
        continue
    if 'transcripts' in p or 'T242-transcripts' in p:
        continue
    print("  MISSED BY THE LINE SWEEP ->", p)
    missed = True
if not missed:
    print("  (none)")
