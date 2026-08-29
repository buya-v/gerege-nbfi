#!/usr/bin/env python3
"""T459 independent citation sweep. For every `conformance.sh:NNNN` citation in the tracked
tree at T454's tip, compare the text at line NNNN in main's conformance.sh with the text at
line NNNN in the tip's. A citation MOVED if the two lines are not byte-identical.
Groups the moved ones by containing file so 'all historical' can be judged rather than asserted.
"""
import re, subprocess, sys, collections, os

REPO = sys.argv[1]
MAIN = open(os.environ["T459_MAIN_CONF"]).read().split("\n")
TIP  = open(os.environ["T459_TIP_CONF"]).read().split("\n")

files = subprocess.run(["git", "-C", REPO, "ls-tree", "-r", "--name-only",
                        "softhouse/T454-longs-route"], capture_output=True, text=True).stdout.split("\n")
pat = re.compile(r'conformance\.sh:(\d{1,5})')
moved = collections.Counter()
total = collections.Counter()
examples = collections.defaultdict(list)

def txt(lines, n):
    return lines[n-1] if 1 <= n <= len(lines) else None

for f in files:
    if not f:
        continue
    blob = subprocess.run(["git", "-C", REPO, "show",
                           "softhouse/T454-longs-route:" + f],
                          capture_output=True)
    if blob.returncode != 0:
        continue
    try:
        s = blob.stdout.decode("utf-8", "replace")
    except Exception:
        continue
    for m in pat.finditer(s):
        n = int(m.group(1))
        total[f] += 1
        a, b = txt(MAIN, n), txt(TIP, n)
        if a != b:
            moved[f] += 1
            if len(examples[f]) < 2:
                examples[f].append((n, (a or "<eof>")[:70], (b or "<eof>")[:70]))

print("citations of the form conformance.sh:NNNN, tip tree")
print("distinct files carrying at least one : %d" % len(total))
print("total occurrences                    : %d" % sum(total.values()))
print("occurrences whose cited LINE TEXT CHANGED between main and the tip: %d" % sum(moved.values()))
print("files affected: %d" % len(moved))
print()
for f in sorted(moved, key=lambda k: -moved[k]):
    print("  %4d moved / %4d total   %s" % (moved[f], total[f], f))
