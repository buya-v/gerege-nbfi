#!/usr/bin/env python3
"""T259 battery helper: plant a shell script carrying the exact fail-open shapes P-80 bans, so the
fail-open lint can be driven RED. A lint nobody has seen fail is not a lint.

The planted file is written to a scratch path OUTSIDE the committed tree; the battery deletes it.

usage: plant_failopen.py <out.sh>
"""
import sys

BANNED_ONE = "|" + "| true"
BANNED_TWO = "|" + "| echo 0"
DEVNULL = "2>" + "/dev/null"

body = "\n".join([
    "#!/usr/bin/env bash",
    "# deliberately missing: set -euo pipefail",
    "n=$(git grep -c PATTERN FILE " + BANNED_TWO + ")",
    "grep -q thing file " + BANNED_ONE,
    "rg other file " + DEVNULL,
    "",
])
with open(sys.argv[1], "w") as fh:
    fh.write(body)
print(f"planted {sys.argv[1]}")
