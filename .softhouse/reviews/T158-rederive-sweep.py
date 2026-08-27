#!/usr/bin/env python3
# T158 — re-derive T156's sweep with an INDEPENDENT enumerator (git ls-files, not
# os.walk) and NAME the 19 "guarded" hits that T156's own transcript does not print.
import os, re, subprocess, sys
REPO = "/tmp/t158-clone"
MUTATE = [
    ("sh:mv", re.compile(r"(?m)^[^#\n]*(?<![\w./-])mv\s")),
    ("sh:cp", re.compile(r"(?m)^[^#\n]*(?<![\w./-])cp\s")),
    ("sh:sed-i", re.compile(r"(?m)^[^#\n]*sed\s+(-[a-zA-Z]*\s+)*-i")),
    ("sh:git-checkout", re.compile(r"(?m)^[^#\n]*git\s+checkout\s+--")),
    ("sh:git-restore", re.compile(r"(?m)^[^#\n]*git\s+(restore|stash)\b")),
    ("py:shutil", re.compile(r"(?m)^[^#\n]*shutil\.(move|copy|copy2|copyfile|copytree|rmtree)\s*\(")),
    ("py:os-rename", re.compile(r"(?m)^[^#\n]*os\.(replace|rename|remove|unlink)\s*\(")),
    ("py:write", re.compile(r"(?m)^[^#\n]*open\s*\([^)]*[\"'][rwa]?[+]?[bt]?w")),
    ("py:write_text", re.compile(r"(?m)^[^#\n]*\.write_(text|bytes)\s*\(")),
]
TARGETS = [
    ("STORE", re.compile(r"\.softhouse/vectors|STORE_ROOT|\$STORE\b|/vectors/")),
    ("PORT", re.compile(r"nexus/internal|\.go\b")),
    ("CAPTURE", re.compile(r"\.softhouse/capture|/out/|capture_dir|OUTDIR|\$O\b|\$OUT\b")),
    ("RIG", re.compile(r"attest\.py|conformance\.sh|contract\.go|PIN\.json|capabilities\.json")),
]
GUARD = re.compile(r"(?m)^[^#\n]*(\btrap\b|\bfinally\s*:|atexit\.register|__exit__|contextmanager)")

files = [f for f in subprocess.run(["git", "-C", REPO, "ls-files", "--", ".softhouse"],
                                   capture_output=True, text=True).stdout.split()
         if f.endswith((".sh", ".py"))]
print("enumerator: git ls-files -> %d .sh/.py files" % len(files))
hits, guarded = 0, []
for rel in sorted(files):
    src = open(os.path.join(REPO, rel), encoding="utf-8", errors="strict").read()
    if not any(rx.search(src) for _, rx in MUTATE):
        continue
    if not any(rx.search(src) for _, rx in TARGETS):
        continue
    hits += 1
    if GUARD.search(src):
        guarded.append((rel, [n for n, rx in TARGETS if rx.search(src)],
                        len(re.findall(r"(?m)^\s*trap\s", src)),
                        len(re.findall(r"(?m)^\s*finally\s*:", src)),
                        len(re.findall(r"atexit\.register", src))))
print("hits=%d  guarded=%d  unguarded=%d" % (hits, len(guarded), hits - len(guarded)))
print()
print("THE GUARDED HITS, NAMED (T156's transcript names only the 4 that touch STORE):")
for rel, tg, ntrap, nfin, natx in guarded:
    print("  %-66s targets=%-22s trap=%d finally=%d atexit=%d"
          % (rel, ",".join(tg), ntrap, nfin, natx))
