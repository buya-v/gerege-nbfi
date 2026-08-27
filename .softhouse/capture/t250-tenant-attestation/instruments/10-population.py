#!/usr/bin/env python3
"""T250 instrument 10 -- population sweep for the T245 F-2 defect class.

DEFECT CLASS (T245 F-2): a capture script SENDS a header from a shell variable
(`-H "$T"`) but WRITES the corresponding attestation line into the committed
`.http` sidecar as a HARD-CODED LITERAL.  The sidecar therefore cannot disagree
with the run it documents.

BOTH TERMS ARE REPORTED (P-67):
  TERM 1 (denominator) = tracked scripts that talk to the reference oracle
          (curl / psql) AND emit at least one `Key: value` attestation line.
  TERM 2 (numerator)   = of those, how many emit AT LEAST ONE attestation line
          whose value is a LITERAL while a variable holding that same value was
          in scope (assigned in the file, or in a file it sources).

SCOPE OF SEARCH (P-66/P-70 -- this is a statement about the search, not the world):
  every path in `git ls-files` of THIS worktree ending `.sh` or `.py`.
  Untracked files, other suffixes, and other checkouts are NOT searched.

ENGINE (P-75): pure `python3` `re` over bytes read from disk.  No `grep`, no
`rg`, no `git grep`.  Calibrated on a known POSITIVE and a known NEGATIVE that
differ by exactly the defect; either arm disagreeing ABORTS the run (exit 4).
`git ls-files` failure ABORTS (exit 5) -- an error is not an empty population.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.realpath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "..", "..")
)

# An attestation line: `echo "Name-Like-This: value"` (or printf/print of one).
# Key must look like an HTTP header or a record key: alnum + dash + underscore.
ATTEST_RE = re.compile(
    r"""(?P<cmd>\becho\b|\bprintf\b|\bprint\b)      # emitter
        \s*\(?\s*
        (?P<q>["'])                                  # opening quote
        (?P<key>[A-Za-z][A-Za-z0-9_-]*)              # key
        :\s
        (?P<val>[^"']*?)                             # value
        (?P=q)""",
    re.VERBOSE,
)

# Shell variable assignment, incl. quoted forms.  `export A B C` is not an
# assignment and is deliberately not matched.
ASSIGN_RE = re.compile(
    r"""^[ \t]*(?:export[ \t]+)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)=
        (?:'(?P<sq>[^']*)'|"(?P<dq>[^"]*)"|(?P<bare>[^\s;#]*))""",
    re.VERBOSE | re.MULTILINE,
)

# `. "$DIR/env.sh"` / `source ./lib.sh` -- resolved relative to the sourcing file.
SOURCE_RE = re.compile(
    r"""^[ \t]*(?:\.|source)[ \t]+["']?(?:\$\{?[A-Za-z_][A-Za-z0-9_]*\}?/)?"""
    r"""(?P<rel>[A-Za-z0-9_./-]+\.sh)["']?""",
    re.MULTILINE,
)

ORACLE_RE = re.compile(r"\bcurl\b|\bpsql\b")


def read(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8", "replace")


def assignments(text):
    """name -> [values], for every literal assignment in `text`."""
    out = {}
    for m in ASSIGN_RE.finditer(text):
        val = m.group("sq")
        if val is None:
            val = m.group("dq")
        if val is None:
            val = m.group("bare")
        if val is None:
            continue
        out.setdefault(m.group("name"), []).append(val)
    return out


def in_scope_vars(path, text, depth=0):
    """Assignments visible to `path`: its own, plus those of files it sources."""
    scope = assignments(text)
    if depth >= 3:
        return scope
    base = os.path.dirname(path)
    for m in SOURCE_RE.finditer(text):
        cand = os.path.normpath(os.path.join(base, os.path.basename(m.group("rel"))))
        if os.path.isfile(cand):
            for k, v in in_scope_vars(cand, read(cand), depth + 1).items():
                scope.setdefault(k, []).extend(v)
    return scope


def attest_lines(text):
    """Every emitted `Key: value` line whose value is a LITERAL (no expansion)."""
    hits = []
    for m in ATTEST_RE.finditer(text):
        key, val = m.group("key"), m.group("val")
        if not val.strip():
            continue
        # `$` / `%` / `{` anywhere in the value means it is derived, not constant.
        if "$" in val or "%" in val or "{" in val:
            continue
        line_no = text.count("\n", 0, m.start()) + 1
        hits.append((line_no, key, val, m.group(0)))
    return hits


def shadowing_var(scope, key, val):
    """An in-scope variable that already carried this attestation value.

    Two shapes count as 'a variable was available':
      (a) the variable's value IS the full `Key: value` header, e.g.
          T='Fineract-Platform-TenantId: gerege';
      (b) the variable's value IS the bare value, e.g. TENANT='gerege'.
    """
    full = "%s: %s" % (key, val)
    for name, vals in sorted(scope.items()):
        for v in vals:
            if v.strip() == full:
                return name, "full-header"
    for name, vals in sorted(scope.items()):
        for v in vals:
            if v.strip() == val.strip() and len(val.strip()) >= 3:
                return name, "bare-value"
    return None


def calibrate():
    """POSITIVE and NEGATIVE arms.  Disagreement ABORTS; never a silent pass."""
    pos = (
        "T='Fineract-Platform-TenantId: gerege'\n"
        'curl -H "$T" x\n'
        'echo "Fineract-Platform-TenantId: gerege" > f\n'
    )
    neg = (
        "T='Fineract-Platform-TenantId: gerege'\n"
        'curl -H "$T" x\n'
        'echo "$T" > f\n'
    )
    p_scope = assignments(pos)
    p_hits = [h for h in attest_lines(pos) if shadowing_var(p_scope, h[1], h[2])]
    n_scope = assignments(neg)
    n_hits = [h for h in attest_lines(neg) if shadowing_var(n_scope, h[1], h[2])]
    if len(p_hits) != 1:
        sys.stderr.write(
            "CALIBRATION FAILED (positive arm): expected 1 flagged, got %d\n" % len(p_hits)
        )
        sys.exit(4)
    if len(n_hits) != 0:
        sys.stderr.write(
            "CALIBRATION FAILED (negative arm): expected 0 flagged, got %d\n" % len(n_hits)
        )
        sys.exit(4)
    print("CALIBRATION: positive arm flagged 1/1, negative arm flagged 0/1")
    print("             the two arms differ by exactly `$` -- instrument DISCRIMINATES")


def main():
    calibrate()
    proc = subprocess.run(["git", "-C", ROOT, "ls-files"], capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(
            "ABORT: git ls-files failed rc=%d: %s\n" % (proc.returncode, proc.stderr)
        )
        sys.exit(5)
    tracked = proc.stdout.splitlines()
    scripts = [p for p in tracked if p.endswith(".sh") or p.endswith(".py")]

    term1 = []
    term2 = []
    unreadable = []
    for rel in scripts:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            unreadable.append(rel)
            continue
        try:
            text = read(path)
        except Exception as exc:
            unreadable.append("%s (%s)" % (rel, exc))
            continue
        hits = attest_lines(text)
        if not hits:
            continue
        if not ORACLE_RE.search(text):
            continue
        term1.append(rel)
        scope = in_scope_vars(path, text)
        flagged = []
        for line_no, key, val, _raw in hits:
            sv = shadowing_var(scope, key, val)
            if sv:
                flagged.append((line_no, key, val, sv[0], sv[1]))
        if flagged:
            term2.append((rel, flagged))

    print("")
    print("SCOPE: git ls-files of %s ; suffix .sh or .py" % ROOT)
    print("tracked files                                : %d" % len(tracked))
    print("  of which .sh or .py                        : %d" % len(scripts))
    print("  unreadable / missing on disk               : %d" % len(unreadable))
    for u in unreadable:
        print("      SKIPPED-UNREADABLE %s" % u)
    print("")
    print(
        "TERM 1  scripts that talk to the oracle AND write >=1 `Key: value` "
        "attestation line: %d" % len(term1)
    )
    for p in term1:
        print("    %s" % p)
    print("")
    print("TERM 2  of those, scripts writing >=1 attestation line as a LITERAL while a")
    print(
        "        variable carrying that same value was IN SCOPE"
        "                          : %d" % len(term2)
    )
    for p, flagged in term2:
        print("    %s" % p)
        for line_no, key, val, var, how in flagged:
            print(
                "        line %-4d  %s: %s   <- shadowed by $%s (%s)"
                % (line_no, key, val, var, how)
            )
    print("")
    print("RATE: %d / %d" % (len(term2), len(term1)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
