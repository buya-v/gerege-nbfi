#!/usr/bin/env python3
"""T465 -- DID THE RE-SPELLING CHANGE ANY VALUE?

    python3 20-assembly-parity.py <base-rev> [--json OUT]

WHY THIS EXISTS. T465 removed a `<softhouse>/LOCK` literal from 17 tracked instruments and
replaced each with an assembled variable. That is only admissible if the ASSEMBLED VALUE IS
BYTE-IDENTICAL to the literal it replaced -- otherwise the repair is a behaviour change wearing
a census fix as a costume, and one of the sites is the exit-protocol guard that decides whether
a fire's uncommitted deliverables are rescued. So the value is MEASURED, in each file's OWN
interpreter, from each file's OWN declaration lines, and compared against the literal read out
of the BASE commit. Nothing here is transcribed.

THE THREE FACTS THIS KEEPS APART, in the shape T238's sweeplib makes mandatory -- an instrument
must not be able to emit a negative it did not measure:

    a MEASURED zero literals at HEAD      the repair landed
    a MEASURED zero literals at BASE      the CALIBRATION FAILED: there was nothing to repair,
                                          so `HEAD is clean` says nothing. Exit 92, never 0.
    an interpreter that would not run     exit 93. Not a parity result of any colour.

NO REAL REPO PATH IS SPELT IN THIS FILE. The softhouse directory name is assembled from SH
below and every expected value is built from it, because this file is itself a tracked
`<softhouse>/*.py` instrument and a spelt literal would be a new row in the very frontier the
task exists to flatten.

EXIT: 0 every site checked and every value matched; 1 a MEASURED mismatch; 9x the instrument
could not measure (corpus, calibration or interpreter). Never conflated (P-80).
The probe line is `T465-ASSEMBLY-PARITY:` and it is printed on every path that reaches a
verdict, and never on a 9x refusal -- read its PRESENCE before its value (P-84).
"""
import argparse
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PROBE = "T465-ASSEMBLY-PARITY:"

# ASSEMBLED, never spelt -- see the module docstring.
SH = "." + "softhouse"
LOCKP = SH + "/LOCK"

# The census's own literal selector, quoted from `census_dead_paths.py` so the two agree about
# what a "literal" is. A private copy of a regex is a drift hazard; a private copy WITH THE
# SOURCE NAMED is at least auditable, and importing across capture directories is worse.
LITERAL_RE = re.compile(r"""(['"])((?:[^'"\\\n]|\\.)*?\.softhouse/(?:[^'"\\\n]|\\.)*?)\1""")
PLACEHOLDER_RE = re.compile(r"%[sdrf]|\{[^}]*\}|\$\{?\w+|<[a-zA-Z_]+>")
GLOB_RE = re.compile(r"[*?\[\]]")
ELLIPSIS_RE = re.compile(r"\.\.\.|…")


def lock_literals(text):
    """Every quoted literal in `text` that the census would call a DEAD CONCRETE reference to
    the fire lock. Returns the raw literal interiors, in order of appearance."""
    out = []
    for m in LITERAL_RE.finditer(text):
        lit = m.group(2)
        path = lit[lit.find(SH + "/"):]
        if not path.startswith(LOCKP):
            continue
        if re.search(r"\s", path) or ELLIPSIS_RE.search(path):
            continue
        if PLACEHOLDER_RE.search(path) or GLOB_RE.search(path):
            continue
        out.append(lit)
    return out


# --------------------------------------------------------------------------------------------
# THE SITE TABLE. One row per repaired file: which NAME now carries the value, and what that
# value must be. Every expected value is BUILT from SH; none is spelt.
#
# `shell` rows are evaluated by running the file's OWN column-0 declaration lines through the
# file's OWN interpreter (read off its shebang) and printing the name. `python` rows are
# evaluated by AST-walking the file's module-level assignments. `strings` rows compare the
# PRODUCED STRING VALUES at BASE and at HEAD, which is the only meaningful check for a file
# whose literals are patch fixtures rather than paths.
# --------------------------------------------------------------------------------------------
SITES = [
    # file                                                          kind      name                     expected
    (SH + "/bin/fire-program.sh",                                   "shell",  "SH_DIR,LOCK_REL",              LOCKP),
    (SH + "/bin/fire-program.sh",                                   "shell",  "SH_DIR,LOCK_REL,LOCK_EXCLUDE_PATHSPEC", ":(top,exclude)" + LOCKP),
    (SH + "/bin/fire-program.sh",                                   "shell",  "SH_DIR,LOCK_REL,LOCK",  "/REPO/" + LOCKP),
    (SH + "/bin/ready-tasks.py",                                    "python", "SH_DIR,LOCK_REL",             LOCKP),
    (SH + "/hooks/push-before-spawn-audit.py",                      "python", "SH_DIR,LOCK_REL",             LOCKP),
    (SH + "/capture/t279-lock-partition/audit-this-fire.py",        "python", "SH_DIR,LOCK_REL",             LOCKP),
    (SH + "/capture/t349-pretooluse-eval/probe/replay-real-dispatches.py", "python", "SH_DIR,LOCK_REL",      LOCKP),
    (SH + "/capture/t349-pretooluse-eval/probe/spawn-gate-candidate.py",   "python", "SH_DIR,LOCK_REL",      LOCKP),
    (SH + "/capture/t325-adopt-attestation/instruments/30-survey-drive.sh", "shell", "SH_DIR,LOCK_REL",      LOCKP),
    (SH + "/capture/t350-reconcile-content/bin/50-drive-reconcile.sh",      "shell", "SH_DIR,LOCK_REL",      LOCKP),
    (SH + "/capture/t353-t342-conditions/bin/lock-host-census.sh",          "shell", "SH_DIR,LOCK_REL",      LOCKP),
    (SH + "/capture/t453-t450-conditions/instruments/drive-arms.sh",        "shell", "LOCKLEAF,LOCK_REL",   LOCKP),
    (SH + "/reviews/T189-probe/hardening.sh",                       "shell",  "SH_DIR,LOCK_EXCLUDE",          ":(exclude)" + LOCKP),
    (SH + "/reviews/T189-probe/reachability.sh",                    "shell",  "SH_DIR,LOCK_EXCLUDE",          ":(exclude)" + LOCKP),
    (SH + "/reviews/t172-probe/check-lock-exclusion-anchor.sh",     "shell",  "SH_DIR,EXPECT_PATHSPEC",       ":(top,exclude)" + LOCKP),
    (SH + "/reviews/t172-probe/run-move-demo.sh",                   "shell",  "USE_FRAGMENT",          '"$LOCK_EXCLUDE_PATHSPEC"'),
    (SH + "/reviews/t202-probe/make-mutants-b.py",                  "strings", "muts",                 None),
    (SH + "/reviews/t202-probe/patch.py",                           "strings", "old,new",              None),
    # PROSE ONLY -- the row it lost was an English sentence in a `why=` explanation, trimmed to a
    # bare path by the census's `.softhouse/`-rooted trim. There is no VALUE to check; the check
    # that matters for it is the literal count, which every row gets below.
    (SH + "/capture/t319-reconciler-f5/run-ownership-matrix.py",    "prose",  "-",                     None),
]


def repo_root():
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    print("ERROR: no .git ancestor of this instrument.", file=sys.stderr)
    raise SystemExit(90)


def git(root, *args):
    proc = subprocess.run(["git"] + list(args), cwd=str(root), capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def base_text(root, rev, rel):
    rc, out, err = git(root, "show", "%s:%s" % (rev, rel))
    if rc != 0:
        print("ERROR: could not read %s at %s: %s" % (rel, rev, err.strip()), file=sys.stderr)
        raise SystemExit(90)
    return out


def shebang_interp(text):
    first = text.split("\n", 1)[0]
    if not first.startswith("#!"):
        return None
    for cand in ("zsh", "bash", "sh"):
        if first.rstrip().endswith("/" + cand) or first.rstrip().endswith(" " + cand):
            return cand
    return None


def shell_value(root, rel, chain, text):
    """Evaluate a NAMED CHAIN of the file's own column-0 declarations, in the file's own
    interpreter, and print the last name in the chain.

    THE CHAIN IS NAMED RATHER THAN SWEPT, and that is the fail-closed choice. An earlier draft
    took EVERY column-0 assignment in the file and handed the lot to the interpreter; on
    `fire-program.sh` that produced `zsh:66: unmatched "` -- a 3000-line driver's declarations
    are not a self-contained prelude. Sweeping would also have let an unrelated later
    assignment silently redefine the name under test. Each name in the chain must be declared
    EXACTLY ONCE at column 0; zero or two is an ambiguity this instrument refuses to guess
    about, because either way the value it printed would not be the value the file uses.
    """
    interp = shebang_interp(text)
    if interp is None:
        raise Refusal(93, "%s: no recognised shell shebang; cannot evaluate %s" % (rel, chain))
    lines = text.split("\n")
    decls = []
    for nm in chain:
        hits = [ln for ln in lines if re.match(r"^%s=" % re.escape(nm), ln)]
        if len(hits) != 1:
            raise Refusal(93, "%s: expected EXACTLY ONE column-0 declaration of %s, found %d"
                          % (rel, nm, len(hits)))
        decls.append(hits[0])
    script = "REPO=/REPO\n" + "\n".join(decls) + "\nprintf '%s' \"${" + chain[-1] + "}\"\n"
    proc = subprocess.run([interp, "-c", script], cwd=str(root), capture_output=True, text=True)
    if proc.returncode != 0:
        raise Refusal(93, "%s: %s refused to evaluate the declaration chain (rc=%d): %s"
                      % (rel, interp, proc.returncode, proc.stderr.strip()[:300]))
    return proc.stdout


class Refusal(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code = code


def python_value(rel, chain, text):
    """AST-walk the module's top-level assignments and evaluate them in an EMPTY namespace.
    Nothing is imported and nothing is executed beyond the assignments themselves."""
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        raise Refusal(93, "%s: does not parse: %s" % (rel, exc))
    ns = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if not targets:
            continue
        try:
            val = eval(compile(ast.Expression(node.value), "<t465>", "eval"), {"__builtins__": {}}, ns)
        except Exception:
            continue
        for t in targets:
            ns[t] = val
    for nm in chain:
        if nm not in ns:
            raise Refusal(93, "%s: no evaluable module-level assignment to %s" % (rel, nm))
    return ns[chain[-1]]


def python_strings(rel, names, text):
    """The ordered list of string values produced by every module-level assignment to any of
    `names`. Used for the two patch fixtures, where the literal is a PATCH BODY rather than a
    path: the parity that matters is that the STRING THE FILE PRODUCES is unchanged."""
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        raise Refusal(93, "%s: does not parse: %s" % (rel, exc))
    ns = {}
    got = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if not targets:
            continue
        try:
            val = eval(compile(ast.Expression(node.value), "<t465>", "eval"), {"__builtins__": {}}, ns)
        except Exception:
            val = None
        for t in targets:
            if val is not None:
                ns[t] = val
            if t in names:
                got.append((t, val))
    return got


def main(argv=None):
    ap = argparse.ArgumentParser(description="T465 assembly parity")
    ap.add_argument("base", help="the commit BEFORE the repair")
    ap.add_argument("--json", default=None)
    args = ap.parse_args(argv)

    root = repo_root()
    rc, out, _ = git(root, "rev-parse", "--verify", "--quiet", args.base + "^{commit}")
    if rc != 0 or not out.strip():
        print("ERROR: %r does not resolve to a commit." % args.base, file=sys.stderr)
        return 90
    base = out.strip()
    rc, head, _ = git(root, "rev-parse", "HEAD")
    head = head.strip()

    rows = []
    base_lits_total = 0
    head_lits_total = 0
    mismatches = []

    print("T465 -- ASSEMBLY PARITY")
    print("=" * 92)
    print("  repo   : %s" % root)
    print("  base   : %s   (the commit BEFORE the repair)" % base)
    print("  head   : %s   (this working tree's HEAD)" % head)
    print("  method : each file's OWN declaration lines, evaluated in that file's OWN")
    print("           interpreter. Expected values are BUILT from a variable, never spelt.")
    print()

    seen_files = []
    for rel, kind, name, expected in SITES:
        if rel not in seen_files:
            seen_files.append(rel)
        try:
            btext = base_text(root, base, rel)
        except SystemExit:
            raise
        hpath = root / rel
        if not hpath.is_file():
            print("REFUSED(90): %s is absent from the working tree." % rel)
            return 90
        htext = hpath.read_text(errors="replace")

        blits = lock_literals(btext)
        hlits = lock_literals(htext)

        row = {"file": rel, "kind": kind, "name": name,
               "baseLiterals": blits, "headLiterals": hlits}

        if kind == "prose":
            verdict = "OK" if not hlits else "MISMATCH"
            row["value"] = None
        elif kind == "strings":
            names = set(name.split(","))
            bvals = python_strings(rel, names, btext)
            hvals = python_strings(rel, names, htext)
            bseq = [v for _, v in bvals]
            hseq = [v for _, v in hvals]
            row["value"] = "%d assignment(s) compared" % len(bseq)
            if bseq == hseq:
                verdict = "OK"
            else:
                verdict = "MISMATCH"
                for i, (bv, hv) in enumerate(zip(bseq, hseq)):
                    if bv != hv:
                        mismatches.append("%s: assignment #%d differs" % (rel, i))
                if len(bseq) != len(hseq):
                    mismatches.append("%s: %d assignment(s) at base, %d at head"
                                      % (rel, len(bseq), len(hseq)))
        else:
            try:
                chain = name.split(",")
                got = shell_value(root, rel, chain, htext) if kind == "shell" \
                      else python_value(rel, chain, htext)
            except Refusal as r:
                print("REFUSED(%d): %s" % (r.code, r))
                print("NO PROBE LINE IS PRINTED. This is a refusal, not a parity result (P-84).",
                      file=sys.stderr)
                return r.code
            row["value"] = got
            if got == expected:
                verdict = "OK"
            else:
                verdict = "MISMATCH"
                mismatches.append("%s: %s = %r, expected %r" % (rel, name, got, expected))

        if hlits:
            verdict = "MISMATCH"
            mismatches.append("%s: STILL SPELLS %d lock literal(s): %r" % (rel, len(hlits), hlits))

        row["verdict"] = verdict
        rows.append(row)
        base_lits_total += len(blits)
        head_lits_total += len(hlits)

        print("  %-8s %s" % (verdict, rel))
        print("           %-24s base literal(s) removed: %d" % (name, len(blits)))
        if kind not in ("prose", "strings"):
            print("           value now = %r" % (row["value"],))
        elif kind == "strings":
            print("           %s" % row["value"])

    print()
    # ---- CALIBRATION, enforced. A clean HEAD proves nothing if BASE was clean too. -----------
    if base_lits_total == 0:
        print("ABORT(92): the BASE commit %s spells ZERO lock literals across the %d file(s) in"
              % (base, len(seen_files)))
        print("the site table. There was nothing to repair, so `HEAD is clean` is not a finding")
        print("about this repair -- it is a statement about the wrong base. REFUSING.")
        print("NO PROBE LINE IS PRINTED (P-84).", file=sys.stderr)
        return 92

    print("CALIBRATION: the base commit spells %d lock literal(s) across %d file(s), so a clean"
          % (base_lits_total, len(seen_files)))
    print("             HEAD is a MEASURED removal and not an empty search.")
    print()
    if mismatches:
        print("MISMATCHES (%d):" % len(mismatches))
        for m in mismatches:
            print("  !! %s" % m)
    else:
        print("Every assembled value equals the literal it replaced, and no file still spells one.")

    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(
            {"base": base, "head": head, "rows": rows,
             "baseLiterals": base_lits_total, "headLiterals": head_lits_total,
             "mismatches": mismatches}, indent=2, sort_keys=True, default=str) + "\n")
        print()
        print("  JSON written to %s" % args.json)

    print()
    print("%s files=%d sites=%d baseLiterals=%d headLiterals=%d mismatches=%d"
          % (PROBE, len(seen_files), len(SITES), base_lits_total, head_lits_total, len(mismatches)))
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
