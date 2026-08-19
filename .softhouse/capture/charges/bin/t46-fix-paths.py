#!/usr/bin/env python3
"""T46 -- close T44 finding A-7.

A-7: "15 of 19 bin/ scripts hard-code T40's ephemeral worktree path, so the shipped run
recipe breaks the moment softhouse prunes that worktree.  A recipe that cannot be re-run is
not a recipe."

This rewrites the hard-coded worktree root to one DERIVED FROM THE SCRIPT'S OWN LOCATION,
overridable with $T40_WORKTREE.  It changes NO request, NO response and NO recorded value --
only where the scripts look for themselves.  The fix is proved by re-running `capture.sh`
into a fresh directory and diffing all 21 responses against the committed ones
(`bin/t46-reissue-identity.sh`).

Run once; it is idempotent.
"""
import pathlib
import re
import sys

BIN = pathlib.Path(__file__).resolve().parent
STALE = "/Users/buv/gerege-nbfi/.claude/worktrees/agent-aae6901cc4f028513"

SH_DEFAULT = (
    'W="${T40_WORKTREE:-$(cd "$(dirname "$0")/../../../.." && pwd)}"'
)
PY_DEFAULT = (
    'W = os.environ.get("T40_WORKTREE",\n'
    '                   str(pathlib.Path(__file__).resolve().parents[4]))'
)

changed = []
for p in sorted(BIN.glob("*")):
    if p.name == "t46-fix-paths.py" or not p.is_file():
        continue
    text = p.read_text()
    if STALE not in text:
        continue
    orig = text

    if p.suffix == ".py":
        text = re.sub(rf'^W = "{re.escape(STALE)}"$', PY_DEFAULT, text, flags=re.M)
        text = text.replace(f'"{STALE}"', PY_DEFAULT.split("=", 1)[1].strip())
        # make sure the imports the replacement needs are present
        if PY_DEFAULT.splitlines()[0] in text:
            for mod in ("os", "pathlib"):
                if not re.search(rf"^import {mod}$", text, flags=re.M):
                    text = re.sub(r"^(import |from )", f"import {mod}\n\\1", text,
                                  count=1, flags=re.M)
    else:
        # capture.sh sources lib.sh by absolute path
        text = text.replace(f". {STALE}/.softhouse/capture/charges/bin/lib.sh",
                            '. "$(dirname "$0")/lib.sh"')
        # VAR=<stale-root>[/suffix]  ->  VAR="<self-located root>[/suffix]"
        def sh_repl(m):
            var, suffix = m.group(1), m.group(2)
            root = 'ROOT'
            return f'{var}="${{T40_WORKTREE:-$(cd "$(dirname "$0")/../../../.." && pwd)}}{suffix}"'
        text = re.sub(rf'^([A-Za-z_][A-Za-z0-9_]*)={re.escape(STALE)}(\S*)$', sh_repl, text, flags=re.M)

    if STALE in text:
        print(f"  !! {p.name}: stale path still present after rewrite", file=sys.stderr)
        sys.exit(1)
    if text != orig:
        p.write_text(text)
        changed.append(p.name)

print("T46 A-7 -- worktree path made self-locating in:")
for c in changed:
    print("  " + c)
print(f"({len(changed)} files rewritten; no request, response or recorded value touched)")
