#!/usr/bin/env python3
import pathlib
root = pathlib.Path(__file__).resolve().parents[3]
tree = root / "nexus" / "internal" / "apps" / "loanschedule"
print("tree:", tree, "exists:", tree.exists())
n=0; dirty=0
for f in sorted(tree.rglob("*.go")):
    n+=1
    b=f.read_bytes()
    nz=[(i,hex(b[i])) for i in range(len(b)) if not (0x20<=b[i]<=0x7e or b[i] in (9,10,13))]
    if nz:
        dirty+=1
        try: b.decode('utf-8'); v="VALID UTF-8"
        except UnicodeDecodeError: v="INVALID UTF-8"
        print("NON-ASCII", f.relative_to(tree), v, nz[:4])
print("go files scanned:", n, "with non-ASCII:", dirty)
