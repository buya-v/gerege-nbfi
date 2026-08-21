#!/usr/bin/env python3
"""T179 — the SECOND engine bug T167 surfaced, demonstrated and driven.

T156's guard classifier is one pattern text.  Run it under Python `re` and it
reports 3 matches on the pre-fix bytes of `.softhouse/reviews/t47-probe/
t47_edit_1.py`; run the same characters under a POSIX ERE engine and it reports 0.
A sweep whose answer depends on which binary executed it is not a measurement.

The pattern is READ OUT OF T156's SOURCE BY THE PARSER — `ast` walks
`t156-sweep-unguarded-mutators.py`, finds the assignment to `GUARD`, and takes the
literal.  It is never retyped here, because a retyped pattern would make this
demonstration about a string I wrote instead of about the one T156 shipped.

Corpus: `git show bf67a85:.softhouse/reviews/t47-probe/t47_edit_1.py` — the immutable
pre-fix blob (P-24: pinned by commit, never via `main:`), plus two minimal inputs that
isolate the mechanism.

Exit 0 only if the divergence is still reproducible.  If every engine agrees, this
script FAILS (exit 1): it exists to demonstrate a disagreement, and a demonstration
that cannot fail is P-22.
"""
import ast
import os
import subprocess
import sys
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
T156 = os.path.join(REPO, ".softhouse", "capture", "pathb", "t149",
                    "t156-sweep-unguarded-mutators.py")
PREFIX_BLOB = "bf67a85:.softhouse/reviews/t47-probe/t47_edit_1.py"


def pattern_from_t156_source():
    """Extract GUARD's literal from T156's AST. Never retyped."""
    tree = ast.parse(open(T156, encoding="utf-8").read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and \
                isinstance(node.targets[0], ast.Name) and \
                node.targets[0].id == "GUARD":
            call = node.value
            if isinstance(call, ast.Call) and call.args and \
                    isinstance(call.args[0], ast.Constant):
                return call.args[0].value, node.lineno
    raise SystemExit("could not find GUARD in %s — refusing to guess" % T156)


def run(cmd, data):
    p = subprocess.run(cmd, input=data, capture_output=True)
    return p.returncode, p.stdout.decode("utf-8", "replace"), \
        p.stderr.decode("utf-8", "replace").strip()


def count_lines(out):
    return len([l for l in out.splitlines() if l])


def engines(pattern, data):
    """(name, note, match_count or None-with-error) for each engine."""
    rows = []

    # 1. Python re, exactly as T156 runs it (whole-buffer, MULTILINE via (?m))
    rows.append(("python re (T156's own engine)", "re.findall on the whole buffer",
                 len(re.findall(pattern, data.decode("utf-8", "replace")))))

    # 2. POSIX ERE via /usr/bin/grep -E.  NOT the shell's `grep`, which in this
    #    environment is a ugrep wrapper — see engine 3.
    ere = pattern.replace("(?m)", "")           # (?m) is a Python-only inline flag
    rc, out, err = run(["/usr/bin/grep", "-cE", ere], data)
    rows.append(("/usr/bin/grep -E (POSIX ERE)",
                 "(?m) stripped: it is not ERE syntax",
                 int(out.strip() or 0) if rc in (0, 1) and not err else "ERR: " + err))

    # 3. Whatever `grep` resolves to for an interactive worker here.
    which = subprocess.run(["/bin/zsh", "-lc", "type grep"], capture_output=True)
    rows.append(("shell `grep` resolves to",
                 which.stdout.decode().split("\n")[0][:70], "-"))
    rc, out, err = run(["/bin/zsh", "-lc",
                        "grep -cE %s" % shquote(ere)], data)
    rows.append(("shell `grep -E` (as typed above)", "same characters again",
                 int(out.strip() or 0) if rc in (0, 1) and out.strip().isdigit()
                 else "ERR: " + (err or out.strip())[:60]))

    # 4. awk, another POSIX ERE implementation
    rc, out, err = run(["/usr/bin/awk", "/" + ere.replace("/", "\\/") + "/ {n++} "
                        "END {print n+0}"], data)
    rows.append(("/usr/bin/awk (POSIX ERE)", "third ERE implementation",
                 int(out.strip() or 0) if rc == 0 and out.strip().isdigit()
                 else "ERR: " + (err or out)[:60]))

    # 5. sed -nE
    rc, out, err = run(["/usr/bin/sed", "-nE", "/" + ere.replace("/", "\\/") + "/p"],
                       data)
    rows.append(("/usr/bin/sed -nE (POSIX ERE)", "fourth ERE implementation",
                 count_lines(out) if rc == 0 else "ERR: " + err[:60]))

    return rows


def shquote(s):
    return "'" + s.replace("'", "'\\''") + "'"


def main():
    pattern, lineno = pattern_from_t156_source()
    print("=== T179 — one pattern, two answers")
    print("pattern source : %s:%d (read via ast, not retyped)"
          % (os.path.relpath(T156, REPO), lineno))
    print("pattern        : %r" % pattern)
    print()

    blob = subprocess.run(["git", "-C", REPO, "show", PREFIX_BLOB],
                          capture_output=True)
    if blob.returncode != 0:
        sys.stderr.write("cannot read %s: %s\n"
                         % (PREFIX_BLOB, blob.stderr.decode()[:200]))
        return 2
    data = blob.stdout
    print("corpus 1       : %s  (%d bytes)" % (PREFIX_BLOB, len(data)))
    rows = engines(pattern, data)
    for name, note, n in rows:
        print("  %-34s %-40s %s" % (name, note, n))
    print()

    py = rows[0][2]
    ere_counts = [r[2] for r in rows if isinstance(r[2], int) and
                  r[0] != "python re (T156's own engine)"]
    print("  python re says %s; the POSIX ERE engines say %s"
          % (py, ", ".join(str(c) for c in ere_counts)))
    print()

    print("--- WHY.  `[^#\\n]` is not the same bracket expression in the two engines.")
    print("    Python re : \\n inside a bracket expression is the NEWLINE escape, so")
    print("                [^#\\n] = 'any char except # and newline'.")
    print("    POSIX ERE : there are no escapes inside a bracket expression, so")
    print("                [^#\\n] = 'any char except #, backslash and the LETTER n'.")
    print("    The anchored [^#\\n]* therefore cannot cross a letter `n`, and every")
    print("    occurrence of `trap` in the corpus has an `n` earlier on its line")
    print("    (`One trap worth ...`).")
    print()

    print("--- The mechanism isolated on two one-line inputs")
    print("    Line 1 has no letter `n` before `trap`; line 2 does. If line 1 matches")
    print("    under an engine and line 2 does not, that engine's zero is caused by")
    print("    `[^#\\n]` and NOT by `\\b` being unsupported — the confound is excluded")
    print("    by measurement rather than by assertion.")
    ere = pattern.replace("(?m)", "")
    minimal = [(b"a trap here\n", "no letter n before `trap`"),
               (b"One trap worth naming\n", "a letter n before `trap`")]
    isolated = []
    for data_m, why in minimal:
        pyn = len(re.findall(pattern, data_m.decode()))
        rc, out, err = run(["/usr/bin/grep", "-cE", ere], data_m)
        eren = int(out.strip() or 0)
        rc2, out2, _ = run(["/usr/bin/awk", "/" + ere.replace("/", "\\/") +
                            "/ {n++} END {print n+0}"], data_m)
        awkn = int(out2.strip() or 0) if out2.strip().isdigit() else -1
        isolated.append((pyn, eren, awkn))
        print("  %-24s %-28s python re=%d  grep -E=%d  awk=%d"
              % (data_m.decode().strip(), why, pyn, eren, awkn))
    if isolated[0][2] == 0:
        print("  NOTE: awk scores 0 even on the line WITHOUT a letter n, so awk's zero")
        print("        on the corpus is explained by `\\b` (not a word boundary in")
        print("        POSIX ERE), not by the bracket expression. Two different")
        print("        incompatibilities, same single pattern text.")
    print()

    ok_corpus = isinstance(py, int) and any(isinstance(c, int) and c != py
                                            for c in ere_counts)
    ok_minimal = isolated[0][1] == 1 and isolated[1][1] == 0 and \
        isolated[1][0] == 1
    print("DIVERGENCE ON THE REAL CORPUS : %s" % ("REPRODUCED" if ok_corpus
                                                  else "NOT reproduced"))
    print("DIVERGENCE ISOLATED TO `[^#\\n]`: %s" % ("REPRODUCED" if ok_minimal
                                                    else "NOT reproduced"))
    if not (ok_corpus and ok_minimal):
        print()
        print("FAIL — this script exists to demonstrate a disagreement between "
              "engines.\n       Every engine agreeing means the demonstration no "
              "longer holds and the\n       claim in the handoff must be re-derived, "
              "not restated.")
        return 1
    print()
    print("CONSEQUENCE: T156's classifier has no single answer. Its committed number "
          "is\nthe Python-re answer; the same file swept from a shell script would "
          "have\nproduced a different population. Any port of a regex sweep between "
          "Python and\nshell must re-derive its counts, not carry them across.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
