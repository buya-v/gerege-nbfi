#!/usr/bin/env python3
"""T181 -- does T178's SHARED-GUARD IDIOM actually hold where T187 extended it?

The idiom under test: the guard does not live in the file that performs the
write.  It is reached by ONE import hop

    sys.path.insert(0, <dirname^2(__file__)>/t47-probe); import t178_guard

T183's finding D-3 was that a classifier reading a single file scored this
idiom as UNGUARDED.  That is a defect in the CLASSIFIER.  The question this
script asks is the other one, and it is the one that matters:

    IS THE FILE ACTUALLY GUARDED?

Driven against all 25 t41-probe rewriters, with special attention to
`edit2.py` and `edit10.py` -- the two T178 FOUND live and T187 later closed --
and to `edit18.py` / `edit21.py`, which write BOTH protected artefacts through
one shared guard.

SAFETY.  The only invocation used is the DANGEROUS one: no argv at all, cwd =
the repository root.  That is exactly how the pre-fix scripts were reachable
(they hard-wired a RELATIVE path, so repo-root cwd was the loaded gun).  It is
safe post-fix precisely because argv parsing and default-deny happen inside
guard.load() BEFORE the target is resolved or opened.  If that ordering were
wrong this script would prove it by moving the artefacts, which are sha256'd
before and after.
"""
import ast
import hashlib
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
PROBE = os.path.join(REPO, ".softhouse", "reviews", "t41-probe")
ADR_REL = "docs/adr/DEC-1-schedule-generator-adapter.md"
GO_REL = "nexus/internal/apps/loanschedule/contract/contract.go"


def sha256_file(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()


def main():
    adr_abs = os.path.join(REPO, ADR_REL)
    go_abs = os.path.join(REPO, GO_REL)
    adr0, go0 = sha256_file(adr_abs), sha256_file(go_abs)
    print("REPO INTEGRITY BEFORE  DEC-1       %s" % adr0)
    print("REPO INTEGRITY BEFORE  contract.go %s" % go0)
    print()

    files = sorted(f for f in os.listdir(PROBE)
                   if f.startswith("edit") and f.endswith(".py"))
    if not files:
        print("ERROR: inspected ZERO files -- P-35")
        return 3

    refused, leaked, hops = [], [], []
    print("%-14s %-6s %-9s %-12s %s"
          % ("file", "exit", "import", "refusal", "first stderr line"))
    print("-" * 96)

    for f in files:
        p = os.path.join(PROBE, f)
        src = io.open(p, encoding="utf-8", errors="replace").read()

        # --- structural: exactly one import hop, resolved from __file__ ----
        # NOTE, and this is a finding in its own right: the FIRST version of
        # this check was a substring match for
        #     "os.path.dirname(os.path.abspath(__file__))"
        # and it scored 0 of 25 -- every file "UNGUARDED" -- because the real
        # idiom wraps that expression across a line break.  The files were
        # guarded; the DETECTOR was broken.  That is T183's D-3 reproduced
        # accidentally, by me, in the reviewer's own tool.  Only driving the
        # behaviour caught it.  It is now done on the AST.
        try:
            tree = ast.parse(src)
        except SyntaxError:
            tree = None
        imports_guard = 0
        inserts_path = False
        uses_file = False
        if tree is not None:
            for n in ast.walk(tree):
                if isinstance(n, ast.Import):
                    for al in n.names:
                        if al.name == "t178_guard":
                            imports_guard += 1
                elif isinstance(n, ast.ImportFrom) and n.module == "t178_guard":
                    imports_guard += 1
                elif isinstance(n, ast.Call):
                    fn = n.func
                    if isinstance(fn, ast.Attribute) and fn.attr == "insert" \
                            and isinstance(fn.value, ast.Attribute) \
                            and fn.value.attr == "path":
                        inserts_path = True
                        seg = ast.dump(n)
                        if "__file__" in seg:
                            uses_file = True
        one_hop = (imports_guard == 1 and inserts_path and uses_file)
        # the guard must NOT be copied inline
        inline = False
        if tree is not None:
            for n in ast.walk(tree):
                if isinstance(n, ast.FunctionDef) and n.name == "_atomic_write":
                    inline = True
                if isinstance(n, ast.Call):
                    fn = n.func
                    if isinstance(fn, ast.Attribute) and fn.attr == "mkstemp":
                        inline = True
        hops.append((f, one_hop, inline))

        # --- behavioural: the dangerous invocation, no argv, repo-root cwd -
        r = subprocess.run([sys.executable, p], capture_output=True,
                           text=True, errors="replace", cwd=REPO)
        first = (r.stderr.strip().splitlines() or [""])[0][:44]
        is_refusal = (r.returncode == 2)
        if is_refusal:
            refused.append(f)
        else:
            leaked.append((f, r.returncode))
        print("%-14s %-6s %-9s %-12s %s"
              % (f, r.returncode,
                 "1 hop" if one_hop else "NO",
                 "REFUSED" if is_refusal else "*** NOT 2 ***",
                 first))

    print("-" * 96)
    adr1, go1 = sha256_file(adr_abs), sha256_file(go_abs)
    print()
    print("REPO INTEGRITY AFTER   DEC-1       %s  %s"
          % (adr1, "UNCHANGED" if adr1 == adr0 else "*** MOVED ***"))
    print("REPO INTEGRITY AFTER   contract.go %s  %s"
          % (go1, "UNCHANGED" if go1 == go0 else "*** MOVED ***"))
    print()
    print("files driven                        : %d" % len(files))
    print("refused with exit 2 (default-deny)  : %d" % len(refused))
    print("did NOT refuse                      : %d  %s" % (len(leaked), leaked))
    print("reach guard by exactly ONE import hop: %d of %d"
          % (sum(1 for _, h, _ in hops if h), len(files)))
    print("contain an INLINE copy of the guard : %d  %s"
          % (sum(1 for _, _, i in hops if i),
             [f for f, _, i in hops if i]))
    print()
    print("The two T178 FOUND live (closed later by T187):")
    for f in ("edit2.py", "edit10.py"):
        st = "REFUSED exit 2" if f in refused else "*** STILL OPEN ***"
        print("  %-12s %s" % (f, st))
    print("The two that write BOTH artefacts through one shared guard:")
    for f in ("edit18.py", "edit21.py"):
        st = "REFUSED exit 2" if f in refused else "*** STILL OPEN ***"
        print("  %-12s %s" % (f, st))

    if adr1 != adr0 or go1 != go0:
        return 2
    return 0 if not leaked else 1


if __name__ == "__main__":
    sys.exit(main())
