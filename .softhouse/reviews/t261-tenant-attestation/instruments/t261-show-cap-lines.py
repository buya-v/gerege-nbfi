#!/usr/bin/env python3
"""Print, by line number, the tenant/content-type/auth lines of each cap*.sh.

python3 `re` only (P-75).  Reads the files handed to it; no search engine.
"""
import re
import sys

PAT = re.compile(r"TenantId|Content-Type|^\s*T=|^\s*CT=|^\s*A=|Authorization|Accept:")

for p in sys.argv[1:]:
    print("===== %s =====" % p)
    with open(p, "rb") as fh:
        text = fh.read().decode("utf-8", "replace")
    for i, line in enumerate(text.split("\n"), 1):
        if PAT.search(line):
            print("  %4d: %s" % (i, line))
    print("")
