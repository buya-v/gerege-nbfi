#!/usr/bin/env python3
"""T164 -- every json.load/loads CALL SITE in this rig must carry parse_float=.

  python3 guard-parse-float-ast.py                 grade this directory
  python3 guard-parse-float-ast.py --root DIR      grade a scratch copy (red-drive)

  exit 0  every call site inspected is compliant or validly declared
  exit 1  FAIL   -- at least one call site loads money through a binary double
  exit 2  REFUSE -- the guard could not honestly reach a verdict (see below)

WHY THIS FILE EXISTS -- the guard it replaces could not fail
------------------------------------------------------------
`prove-mkreq7-guard-red.py:139-150` asserted the no-float property like this:

    src = open(os.path.join(DIR, "analyze7.py")).read()
    check("it parses JSON numbers as Decimal", "parse_float=decimal.Decimal" in src)

That is a WHOLE-FILE SOURCE GREP.  `parse_float=decimal.Decimal` occurs TWICE in
`analyze7.py`: once at line 39 in the code, and once at line 6 INSIDE THE FILE'S OWN
DOCSTRING.  A2-11 measured the consequence and T164 reproduced it: delete the keyword
from the CODE, leave the docstring alone, and the guard still prints `ok` and exits 0
while `analyze7.py` loads every oracle amount as a binary double.  A guard kept green by
its own prose is P-22 -- a guard that structurally cannot fail -- and this is the
program's sixth recorded instance.

It is also P-35 (phrase the guard positively).  The property is not "does the string
`parse_float` appear somewhere in this file".  The property is:

    EVERY json.load / json.loads CALL SITE PASSES parse_float=, AND THE VALUE IT PASSES
    IS NOT THE BUILTIN float.

so this guard PARSES THE SOURCE and grades CALL SITES, one at a time, by line number.
It does not search text.  A `parse_float` in a docstring, a comment, or a string literal
is invisible to it -- proven on every run by the selector self-test below.

WHAT COUNTS AS A CALL SITE (the selector, checked before the conditions -- P-76 addendum)
------------------------------------------------------------------------------------
Resolved per file from that file's own imports, so an alias cannot hide a site:

    import json                 -> json.load(...)      json.loads(...)
    import json as J            -> J.load(...)         J.loads(...)
    from json import load       -> load(...)
    from json import loads as L -> L(...)

Before it grades anything, the guard runs SELECTOR_SELFTEST below -- a synthetic source
carrying all four alias shapes plus three decoys (the token in a docstring, in a comment,
and in a string literal).  It must find exactly 4 sites and exactly 0 decoys.  If it does
not, the guard REFUSES rather than reporting an absence: a selector that has stopped
selecting cannot produce a measured negative (P-66/P-70).

NIL COVERAGE IS AN ERROR, NEVER A PASS (P-45/P-80)
---------------------------------------------------
Three refusals fire before any verdict, because the fail-open half of the defect above is
a guard that finds nothing and reports success:

  * 0 Python files found under the root            -> REFUSE, exit 2
  * 0 json.load/loads call sites inspected         -> REFUSE, exit 2
  * any file that will not parse                   -> REFUSE, exit 2 (never a silent skip)

THE DECLARATION MECHANISM -- default-deny and enumerable (T207)
----------------------------------------------------------------
T207 ruled that "add parse_float" is sometimes the WRONG repair: a script whose job is to
REPRODUCE a target that loads without parse_float must keep loading the same way, or it
stops reproducing.  So a site may be declared in `PARSE-FLOAT-EXEMPT.txt`.  The register
is not an allowlist and cannot rot into one:

  * DEFAULT-DENY.  A site that is not in the register and has no parse_float is a FAIL.
    An unknown category is a REFUSE, not a skip.
  * ENUMERABLE.  Every record is printed in full on every run, green or red, with its
    category, its reason, and the outcome of its precondition.
  * PINNED.  Each record pins the exact stripped source text of the line it exempts.  If
    the line moves or changes, the record no longer matches and the guard REFUSES.
  * PRECONDITIONED.  Each category carries a machine-checked precondition:
      FROZEN-T114        the file produced committed evidence and may not be edited.
                         VALID ONLY WHILE the file's sha256 still equals the digest
                         MANIFEST.sha256 pins for it, and the named evidence still
                         exists.  Edit the file and the exemption dies with it.
      REPRODUCTION-T207  the site deliberately reproduces a target that loads without
                         parse_float.  VALID ONLY WHILE that target still exists, still
                         has a json.load/loads at the named line, and STILL LACKS
                         parse_float.  Fix the target and the exemption dies.
  * STALE IS AN ERROR.  A record whose site does not exist, or whose site now carries
    parse_float, is a REFUSE.  Nothing here can be left behind quietly.

NOT IN SCOPE, STATED SO THIS IS NOT READ AS EXHAUSTIVE (P-26/P-40)
-------------------------------------------------------------------
This guard grades `.softhouse/capture/tierA-a2/*.py` -- T164's files_hint -- and nothing
else.  The ~74-file `.softhouse/`-wide json.load population is T145.  Money reaching a
binary double by routes OTHER than json.load (a bare float(), a json.dump of a document
parsed that way, a json.load inside a `python3 -c` in a shell script) is R2/R3/R4 in
`census-json-float-siblings.py` and is graded there, not here.  READ-ONLY: writes nothing
but stdout, contacts no oracle.
"""
import ast
import hashlib
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
REGISTER_NAME = "PARSE-FLOAT-EXEMPT.txt"
MANIFEST_NAME = "MANIFEST.sha256"
LOADERS = ("load", "loads")
CATEGORIES = ("FROZEN-T114", "REPRODUCTION-T207")

# A synthetic source with all four alias shapes plus three decoys. Parsed on every run.
SELECTOR_SELFTEST = '''\
"""decoy 1: parse_float=decimal.Decimal in a DOCSTRING."""
import json
import json as J
from json import load
from json import loads as L
# decoy 2: parse_float=decimal.Decimal in a COMMENT.
DECOY3 = "parse_float=decimal.Decimal in a STRING LITERAL."
a = json.load(open("x"))
b = J.loads("{}")
c = load(open("y"))
d = L("{}")
'''


class Refusal(Exception):
    """The guard cannot honestly reach a verdict. Exit 2, never a pass."""


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def loader_names(tree):
    """(dotted-attr prefixes, bare names) that reach json.load/json.loads in this file."""
    mods, bare = set(), set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name == "json":
                    mods.add(a.asname or "json")
        elif isinstance(n, ast.ImportFrom) and n.module == "json":
            for a in n.names:
                if a.name in LOADERS:
                    bare.add(a.asname or a.name)
    return mods, bare


def call_sites(src, filename):
    """[(lineno, col, kind, kwnames, parse_float_expr_or_None)] for every load call site."""
    try:
        tree = ast.parse(src, filename=filename)
    except SyntaxError as e:
        raise Refusal("%s will not parse: %s -- a file the guard cannot read is not a "
                      "file the guard may skip" % (filename, e))
    mods, bare = loader_names(tree)
    out = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        kind = None
        if isinstance(f, ast.Attribute) and f.attr in LOADERS:
            if isinstance(f.value, ast.Name) and f.value.id in mods:
                kind = "%s.%s" % (f.value.id, f.attr)
        elif isinstance(f, ast.Name) and f.id in bare:
            kind = f.id
        if kind is None:
            continue
        kwnames = [k.arg for k in n.keywords if k.arg]
        pf = None
        for k in n.keywords:
            if k.arg == "parse_float":
                pf = k.value
        out.append((n.lineno, n.col_offset, kind, kwnames, pf))
    return sorted(out)


def unparse(node):
    if node is None:
        return None
    try:
        return ast.unparse(node)          # 3.9+
    except AttributeError:                # pragma: no cover
        return ast.dump(node)


def resolves_to_builtin_float(expr_text):
    """`parse_float=float` is a keyword that satisfies a grep and changes nothing."""
    return expr_text in ("float", "builtins.float", "__builtins__.float")


def selector_selftest():
    sites = call_sites(SELECTOR_SELFTEST, "<selector-selftest>")
    lines = SELECTOR_SELFTEST.split("\n")
    found = sorted(s[0] for s in sites)
    want = [8, 9, 10, 11]
    decoy_lines = [i + 1 for i, l in enumerate(lines) if "parse_float" in l]
    if found != want:
        raise Refusal("SELECTOR SELF-TEST FAILED: expected call sites on lines %s, found "
                      "%s. The selector is not selecting; a negative result from it would "
                      "be a statement about the search, not about the rig (P-66)."
                      % (want, found))
    if set(found) & set(decoy_lines):
        raise Refusal("SELECTOR SELF-TEST FAILED: a decoy line %s was graded as a call "
                      "site." % sorted(set(found) & set(decoy_lines)))
    return len(sites), len(decoy_lines)


def read_register(root):
    """[(file, line, category, pinned, detail, reason)] from PARSE-FLOAT-EXEMPT.txt."""
    p = os.path.join(root, REGISTER_NAME)
    if not os.path.exists(p):
        return []
    recs = []
    for lineno, raw in enumerate(open(p), 1):
        line = raw.split("#")[0].strip()
        if not line:
            continue
        parts = [x.strip() for x in line.split("|")]
        if len(parts) != 6:
            raise Refusal("%s:%d is malformed -- expected 6 pipe-separated fields "
                          "(file | line | category | pinned-source | detail | reason), "
                          "got %d: %r" % (REGISTER_NAME, lineno, len(parts), line))
        f, ln, cat, pinned, detail, reason = parts
        if cat not in CATEGORIES:
            raise Refusal("%s:%d declares category %r, which is not one of %s. An "
                          "unrecognised category is a REFUSAL, never a silent skip."
                          % (REGISTER_NAME, lineno, cat, list(CATEGORIES)))
        try:
            ln = int(ln)
        except ValueError:
            raise Refusal("%s:%d has a non-integer line number %r"
                          % (REGISTER_NAME, lineno, ln))
        recs.append((f, ln, cat, pinned, detail, reason))
    return recs


def manifest_digests(root):
    p = os.path.join(root, MANIFEST_NAME)
    if not os.path.exists(p):
        return None
    d = {}
    for line in open(p):
        line = line.rstrip("\n")
        if not line:
            continue
        h, _, rel = line.partition("  ")
        if rel:
            d[rel] = h
    return d


def check_frozen(root, rec, digests):
    f, ln, _cat, _pin, detail, _why = rec
    if not detail.startswith("produced:"):
        return False, ("detail must be `produced:<committed evidence path>`, got %r"
                       % detail)
    ev = detail[len("produced:"):].strip()
    if not os.path.exists(os.path.join(root, ev)):
        return False, "the committed evidence it names, %s, is not on disk" % ev
    if digests is None:
        return False, ("%s is absent, so `frozen` cannot be verified -- an unverifiable "
                       "precondition is denied, not assumed" % MANIFEST_NAME)
    if f not in digests:
        return False, "%s does not pin %s, so it is not a frozen rig file" % (MANIFEST_NAME, f)
    actual = sha256(os.path.join(root, f))
    if actual != digests[f]:
        return False, ("%s HAS BEEN EDITED (sha256 %s, manifest pins %s) -- a file that is "
                       "being edited is not frozen, so add parse_float instead"
                       % (f, actual[:12], digests[f][:12]))
    return True, "frozen: sha256 matches %s; produced %s" % (MANIFEST_NAME, ev)


def check_reproduction(root, rec):
    f, ln, _cat, _pin, detail, _why = rec
    if not detail.startswith("reproduces:"):
        return False, "detail must be `reproduces:<path>:<line>`, got %r" % detail
    spec = detail[len("reproduces:"):].strip()
    tpath, _, tline = spec.rpartition(":")
    if not tpath or not tline.isdigit():
        return False, "cannot read `reproduces:<path>:<line>` out of %r" % spec
    tline = int(tline)
    ap = tpath if os.path.isabs(tpath) else os.path.join(root, tpath)
    if not os.path.exists(ap):
        return False, "the target it reproduces, %s, is not on disk" % tpath
    tsites = call_sites(open(ap).read(), tpath)
    at = [s for s in tsites if s[0] == tline]
    if not at:
        return False, ("%s:%d is not a json.load/loads call site any more -- the "
                       "reproduction has drifted" % (tpath, tline))
    if any(s[4] is not None for s in at):
        return False, ("%s:%d NOW CARRIES parse_float -- the target was fixed, so this is "
                       "no longer a faithful reproduction. Fix this site too."
                       % (tpath, tline))
    return True, "faithful: %s:%d is still a json.load with no parse_float" % (tpath, tline)


def main(argv):
    root = DIR
    if len(argv) >= 3 and argv[1] == "--root":
        root = os.path.abspath(argv[2])
    elif len(argv) > 1:
        sys.stderr.write(__doc__)
        return 2

    print("=" * 78)
    print("T164 -- json.load/loads call-site guard (AST, not source grep)")
    print("=" * 78)
    print("ROOT: %s" % root)
    print()

    n_sites, n_decoys = selector_selftest()
    print("SELECTOR SELF-TEST: %d synthetic call sites found across 4 alias shapes; "
          "%d decoy line(s)" % (n_sites, n_decoys))
    print("  (`parse_float` in a docstring, a comment and a string literal -- all three "
          "invisible to the selector)")
    print()

    if not os.path.isdir(root):
        raise Refusal("root %s is not a directory" % root)
    pyfiles = sorted(n for n in os.listdir(root)
                     if n.endswith(".py") and os.path.isfile(os.path.join(root, n)))
    if not pyfiles:
        raise Refusal("NIL COVERAGE -- 0 Python files under %s. INSPECTED NOTHING. A "
                      "guard that finds nothing and reports success is the defect this "
                      "guard was written to remove (P-45)." % root)

    sites = []          # (file, line, kind, kwnames, pf_text, srcline)
    srclines = {}
    for f in pyfiles:
        src = open(os.path.join(root, f)).read()
        srclines[f] = src.split("\n")
        for ln, _col, kind, kwnames, pf in call_sites(src, f):
            sites.append((f, ln, kind, kwnames, unparse(pf),
                          srclines[f][ln - 1].strip() if ln - 1 < len(srclines[f]) else ""))

    if not sites:
        raise Refusal("NIL COVERAGE -- %d Python file(s) inspected, 0 json.load/loads "
                      "call sites found. INSPECTED NOTHING, so there is nothing to "
                      "certify. This is an ERROR, not a pass (P-45/P-80)." % len(pyfiles))

    register = read_register(root)
    digests = manifest_digests(root)
    by_key = {(f, ln): (f, ln, k, kw, pf, sl) for f, ln, k, kw, pf, sl in sites}

    # ---------------------------------------------------------------- the register
    print("DECLARATION REGISTER (%s) -- %d record(s), every one printed, "
          "default-deny" % (REGISTER_NAME, len(register)))
    exempt = {}
    refusals = []
    for rec in register:
        f, ln, cat, pinned, detail, reason = rec
        key = (f, ln)
        site = by_key.get(key)
        if site is None:
            refusals.append("%s:%d is declared %s but is NOT a json.load/loads call site "
                            "in this rig -- a stale record is an ERROR (P-22): remove it."
                            % (f, ln, cat))
            print("  STALE   %s:%-4d %-18s %s" % (f, ln, cat, "no such call site"))
            continue
        if site[4] is not None:
            refusals.append("%s:%d is declared %s but ALREADY carries parse_float=%s -- "
                            "the record is stale: remove it." % (f, ln, cat, site[4]))
            print("  STALE   %s:%-4d %-18s %s" % (f, ln, cat, "site is already compliant"))
            continue
        if site[5] != pinned:
            refusals.append("%s:%d pinned source has drifted.\n      register: %r\n"
                            "      on disk:  %r" % (f, ln, pinned, site[5]))
            print("  DRIFT   %s:%-4d %-18s pinned source no longer matches" % (f, ln, cat))
            continue
        if cat == "FROZEN-T114":
            ok, why = check_frozen(root, rec, digests)
        else:
            ok, why = check_reproduction(root, rec)
        print("  %s %s:%-4d %-18s %s" % ("ALLOW  " if ok else "DENIED ", f, ln, cat, why))
        print("          reason: %s" % reason)
        if ok:
            exempt[key] = (cat, reason, why)
        else:
            refusals.append("%s:%d declared %s but its precondition FAILED: %s"
                            % (f, ln, cat, why))
    if not register:
        print("  (none)")
    print()

    # ---------------------------------------------------------------- the verdict
    compliant, declared, violations, dodges = [], [], [], []
    for s in sites:
        f, ln, kind, kwnames, pf, sl = s
        if pf is None:
            if (f, ln) in exempt:
                declared.append(s)
            else:
                violations.append(s)
        elif resolves_to_builtin_float(pf):
            dodges.append(s)
        else:
            compliant.append(s)

    print("POPULATION -- both terms (P-67)")
    print("  Python files inspected .................. %d" % len(pyfiles))
    print("  json.load/loads CALL SITES inspected .... %d" % len(sites))
    print("  ... carrying parse_float= ............... %d" % len(compliant))
    print("  ... carrying parse_float=float (a dodge)  %d" % len(dodges))
    print("  ... declared in the register ............ %d" % len(declared))
    print("  ... VIOLATIONS .......................... %d" % len(violations))
    print()

    seen = {}
    for f, ln, kind, kwnames, pf, sl in compliant:
        seen.setdefault(pf, []).append("%s:%d" % (f, ln))
    print("parse_float= VALUE EXPRESSIONS ACTUALLY PASSED (%d distinct) -- listed so a "
          "reader can audit them, not allowlisted" % len(seen))
    for k in sorted(seen):
        print("  %-18s %d site(s): %s" % (k, len(seen[k]), ", ".join(seen[k])))
    print()

    print("EVERY CALL SITE, GRADED")
    for f, ln, kind, kwnames, pf, sl in sites:
        if pf is None and (f, ln) in exempt:
            verdict = "DECLARED %s" % exempt[(f, ln)][0]
        elif pf is None:
            verdict = "VIOLATION"
        elif resolves_to_builtin_float(pf):
            verdict = "VIOLATION (parse_float=float is a no-op)"
        else:
            verdict = "ok"
        print("  %-11s %-32s:%-4d %-11s parse_float=%s"
              % (verdict, f, ln, kind, pf if pf is not None else "MISSING"))
    print()

    if refusals:
        print("REFUSING TO REACH A VERDICT -- %d register problem(s):" % len(refusals),
              file=sys.stderr)
        for r in refusals:
            print("  * %s" % r, file=sys.stderr)
        print("\nEXIT 2 (REFUSE): the declaration register is not in a state where a green "
              "run would mean anything.", file=sys.stderr)
        return 2

    if violations or dodges:
        print("FAIL: %d call site(s) load JSON through a binary double."
              % (len(violations) + len(dodges)), file=sys.stderr)
        for f, ln, kind, kwnames, pf, sl in violations + dodges:
            print("  %s:%d  %s(...)  keywords=%s  ->  %s"
                  % (f, ln, kind, kwnames or "[]",
                     "no parse_float" if pf is None else "parse_float=%s (a no-op)" % pf),
                  file=sys.stderr)
            print("      %s" % sl, file=sys.stderr)
        print("\nAdd `parse_float=decimal.Decimal`, or -- if the site is a FAITHFUL "
              "REPRODUCTION of a target that loads without it (T207) or a T114-frozen "
              "file -- declare it in %s." % REGISTER_NAME, file=sys.stderr)
        return 1

    print("PASS -- %d call site(s) across %d file(s): %d carry parse_float=, %d are "
          "declared and their preconditions hold, 0 violations."
          % (len(sites), len(pyfiles), len(compliant), len(declared)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Refusal as e:
        sys.stdout.flush()
        print("\nREFUSING: %s" % e, file=sys.stderr)
        sys.exit(2)
