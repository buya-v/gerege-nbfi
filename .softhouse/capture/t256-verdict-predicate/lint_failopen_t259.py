#!/usr/bin/env python3
"""T259 -- fail-open lint, pointed FIRST at T259's own instruments.

Last fire three workers put fail-opens into the instruments they wrote to enforce the rule they
had just broken. So this runs against `.softhouse/capture/t256-verdict-predicate/` before it is
pointed anywhere else, and T259's battery fails if it is not clean.

The rules it enforces are written out in prose in `RULES-failopen.md` beside this file. They are
NOT restated here in literal token form, and the regexes below are assembled from fragments, for
one reason: a lint whose own description trips its own rules must either exempt itself or be
permanently red, and BOTH of those are worse than not writing the tokens down twice. Nothing is
excluded from the scan -- this file is scanned like every other, and is expected to come back
clean on its own merits.

THE HATCH, and the way it is NOT allowed to be used
  A line may carry `# lint-failopen: ok -- <reason>` on itself or on the line above. The reason is
  MANDATORY; a bare hatch is itself a finding. The hatch is for a construct whose exit status is
  classified explicitly within a line or two -- which is a different thing from swallowing it.
  Using it to silence the detector while leaving the script able to lie is a rejection.

EXIT: 0 clean, 1 findings (a REAL measured negative, including NIL COVERAGE), 2 error. Never
conflated.
"""
import re
import sys
from pathlib import Path

_P = "|" + "|"
_DN = "2>" + r"\s*" + "/dev/" + "null"
_EXC = "except"
_PASS = "pa" + "ss"

SH_BANNED = [
    (re.escape(_P) + r"\s*true\b", "short-circuit-to-true swallows the exit status"),
    (re.escape(_P) + r"\s*:\s*(?:$|[;)])", "short-circuit-to-noop swallows the exit status"),
    (re.escape(_P) + r"\s*echo\b", "short-circuit-to-echo prints an absence over an error (P-80)"),
    (_DN, "stderr sent to the null device -- an error becomes an absence"),
    (r"\bset\s+\+e\b", "the abort is disarmed here"),
    (r"(?<![\w/.-])grep\b(?!_)", "bare grep is bundled ugrep with hidden --exclude-dir (P-75)"),
    (r"(?<![\w/.-])rg\b", "that tool has no binary here and exits 0 through a pipe (P-75)"),
    (r"git\s+grep\s+-[A-Za-z]*E", r"that flag reads \b as a literal b and returns 0 (P-75)"),
]
PY_BANNED = [
    (_EXC + r"\s*:", "a catch-all handler swallows everything, including the bug"),
    (_EXC + r"[^:\n]*:[ \t]*" + _PASS + r"\b", "the handler discards the failure"),
    (_DN, "stderr sent to the null device -- an error becomes an absence"),
]
HATCH = re.compile(r"#\s*lint-failopen:\s*ok\s*--\s*(?P<reason>\S.*)$")
BARE_HATCH = re.compile(r"#\s*lint-failopen:\s*ok\s*(?:--\s*)?$")


def scan(path: Path):
    findings = []
    text = path.read_text()
    lines = text.splitlines()
    rules = SH_BANNED if path.suffix == ".sh" else PY_BANNED
    for i, line in enumerate(lines, 1):
        if BARE_HATCH.search(line) and not HATCH.search(line):
            findings.append((i, "BARE HATCH -- a hatch with no reason is itself a finding"))
            continue
        if line.lstrip().startswith("#"):
            continue
        hatched = bool(HATCH.search(line)) or (i >= 2 and bool(HATCH.search(lines[i - 2])))
        if hatched:
            continue
        for pat, why in rules:
            if re.search(pat, line):
                findings.append((i, why + f"   [{line.strip()[:88]}]"))
    if path.suffix == ".sh" and "set -euo pipefail" not in text:
        findings.append((0, "missing the strict-mode preamble"))
    return findings


def main() -> int:
    roots = [Path(a) for a in sys.argv[1:]] or [Path(__file__).resolve().parent]
    files, skipped, total = [], 0, 0
    for r in roots:
        if not r.exists():
            print(f"ERROR: no such path: {r}", file=sys.stderr)
            return 2
        for p in sorted(r.rglob("*")):
            if not p.is_file():
                continue
            total += 1
            if p.suffix in (".sh", ".py"):
                files.append(p)
            else:
                skipped += 1

    print("T259 fail-open lint")
    for r in roots:
        print(f"  root            : {r}")
    print(f"  files seen      : {total}")
    print(f"  files SCANNED   : {len(files)}  (.sh and .py, this file included)")
    print(f"  files SKIPPED   : {skipped}  (not .sh/.py -- json, md, txt; counted, P-40)")
    if not files:
        print("  REFUSED: NIL COVERAGE -- scanned zero files. An empty scan is not a clean scan.")
        return 1

    nfind = 0
    for p in files:
        f = scan(p)
        if f:
            print(f"  -- {p}")
            for ln, why in f:
                nfind += 1
                print(f"     line {ln}: {why}")
    print(f"  findings        : {nfind}")
    return 1 if nfind else 0


if __name__ == "__main__":
    sys.exit(main())
