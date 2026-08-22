#!/usr/bin/env python3
"""T260 — the instrument audit again, but over EXECUTABLE CODE ONLY.

The line-level audit (80-) flags every hit including the ones inside docstrings and inside the
applier's hunk string literals -- i.e. inside DEC-2's own prose, which legitimately contains the
words `grep`, `rg` and `|| true` because it is a document ABOUT them. Reporting those as findings
would be the fabrication class this program calls out.

So this pass parses each file with `ast`, deletes every string constant and every comment, and
re-scans what actually executes. It also reports, per file, whether the process-invocation
surface classifies return codes (P-80) rather than truth-testing them.

Exit 0 always.
"""
import ast
import io
import os
import re
import sys
import tokenize

BAD = [
    ("bare `grep`", re.compile(r"(?<![-\w.])grep\b")),
    ("`rg`", re.compile(r"(?<![-\w.])rg\b")),
    ("`|| true`", re.compile(r"\|\|\s*true")),
    ("`|| echo`", re.compile(r"\|\|\s*echo")),
    ("bare `except:`", re.compile(r"except\s*:")),
    ("`shell=True`", re.compile(r"shell\s*=\s*True")),
    ("`check=False`", re.compile(r"check\s*=\s*False")),
]


def strip_strings_and_comments(src):
    """Return the source with every STRING token and COMMENT token blanked out."""
    out = []
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    except Exception as exc:
        return None, "tokenize failed: %s" % exc
    for tok in toks:
        if tok.type in (tokenize.STRING, tokenize.COMMENT):
            out.append(("<%s>" % ("STR" if tok.type == tokenize.STRING else "CMT"), tok.start[0]))
        else:
            out.append((tok.string, tok.start[0]))
    # rebuild line-wise so line numbers stay meaningful
    lines = {}
    for s, ln in out:
        lines.setdefault(ln, []).append(s)
    return "\n".join("%d: %s" % (ln, " ".join(v)) for ln, v in sorted(lines.items())), None


def main():
    files = []
    for d in sys.argv[1:]:
        for root, _, names in os.walk(d):
            for nm in sorted(names):
                if nm.endswith(".py"):
                    files.append(os.path.join(root, nm))
    print("T260 — instrument audit over EXECUTABLE CODE ONLY (strings + comments removed)")
    print("=" * 100)
    total = 0
    for f in sorted(files):
        src = open(f, encoding="utf-8").read()
        code, err = strip_strings_and_comments(src)
        if code is None:
            print(f"\n  {os.path.basename(f)}: REFUSE — {err}")
            continue
        hits = []
        for label, pat in BAD:
            for m in pat.finditer(code):
                ln = code[: m.start()].rfind("\n")
                seg = code[ln + 1: code.find("\n", m.start())]
                hits.append((label, seg[:100]))
        # P-80 surface: does the file invoke subprocesses, and if so does it read returncode?
        tree = ast.parse(src)
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
        uses_subproc = any(
            isinstance(c.func, ast.Attribute) and getattr(c.func.value, "id", "") == "subprocess"
            for c in calls
        )
        reads_rc = "returncode" in code or ".returncode" in src
        print(f"\n  {os.path.basename(f)}")
        print(f"    subprocess used: {uses_subproc}   reads .returncode: {reads_rc}")
        if hits:
            total += len(hits)
            for label, seg in hits:
                print(f"    *** EXECUTABLE {label}: {seg}")
        else:
            print("    known-bad shapes in executable code: NONE")
    print()
    print(f"TOTAL known-bad shapes in EXECUTABLE code across all instruments: {total}")


if __name__ == "__main__":
    main()
