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
                         VALID ONLY WHILE the file is TRACKED IN GIT, the named evidence
                         exists AND is itself pinned in MANIFEST.sha256, and the file's
                         sha256 still equals BOTH the manifest digest AND the digest the
                         record itself pins in field 7.
      REPRODUCTION-T207  the site deliberately reproduces a target that loads without
                         parse_float.  VALID ONLY WHILE that target still exists, still
                         has a json.load/loads at the named line, and STILL LACKS
                         parse_float.  Fix the target and the exemption dies.  The target
                         must be REPO-RELATIVE; absolute and root-escaping paths are
                         refused (T263 F-6).

CORRECTION, T270 -- THIS DOCSTRING USED TO OVERSTATE THE FREEZE
----------------------------------------------------------------
It said "Edit the file and the exemption dies with it."  T263 measured that end to end
(ATTACK-REVIVE.txt): it dies, but it does not STAY dead.  `manifest.py write` regenerates
MANIFEST.sha256 -- a command T164's own task ran -- and the exemption comes back with the
edit still in place.  Field 7 of the register now pins the digest IN THE REGISTER, which
`manifest.py write` cannot touch, so a revival requires a second deliberate edit that
appears in `git diff` on the register.  What is still NOT closed, and is said plainly
rather than implied away: someone willing to commit a new file and cite evidence it did
not produce can still mint an exemption; the remaining control there is review of the
diff.  `produced:` provenance is GRADED (`evidence NAMES its producer` vs `ASSERTED
ONLY`) rather than enforced, because it is only mechanically checkable for 3 of the 6
live records -- re-derived by T270, and NOT what T263 F-5 assumed.
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
    """[(file, line, category, pinned, detail, reason, frozen_sha)] from the register.

    SIX fields is the T164 format; SEVEN adds the durable digest pin T270 added for
    FROZEN-T114 (field 7, or `-` where it does not apply). Six is still accepted so that
    T164's frozen red-driver -- which appends 6-field records and whose transcript must
    stay re-derivable under T114 -- keeps working. A 6-field FROZEN record is graded and
    printed as MANIFEST-ONLY / WEAK rather than silently treated as equivalent.
    """
    p = os.path.join(root, REGISTER_NAME)
    if not os.path.exists(p):
        return []
    recs = []
    for lineno, raw in enumerate(open(p), 1):
        line = raw.split("#")[0].strip()
        if not line:
            continue
        parts = [x.strip() for x in line.split("|")]
        if len(parts) not in (6, 7):
            raise Refusal("%s:%d is malformed -- expected 6 or 7 pipe-separated fields "
                          "(file | line | category | pinned-source | detail | reason "
                          "[| frozen-sha256]), got %d: %r"
                          % (REGISTER_NAME, lineno, len(parts), line))
        if len(parts) == 6:
            parts = parts + [""]
        f, ln, cat, pinned, detail, reason, frozen_sha = parts
        if cat not in CATEGORIES:
            raise Refusal("%s:%d declares category %r, which is not one of %s. An "
                          "unrecognised category is a REFUSAL, never a silent skip."
                          % (REGISTER_NAME, lineno, cat, list(CATEGORIES)))
        try:
            ln = int(ln)
        except ValueError:
            raise Refusal("%s:%d has a non-integer line number %r"
                          % (REGISTER_NAME, lineno, ln))
        recs.append((f, ln, cat, pinned, detail, reason, frozen_sha))
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


def git_tracked(root, rel):
    """(verdict, why). verdict is True/False/None; None = not a git work tree.

    T270/T263-F-4(b): a brand-new unguarded money-shaped loader could be MINTED into the
    register in two commands, naming evidence it never produced. Requiring the exempted
    file to be TRACKED IN GIT does not make that impossible, but it forces the minting
    into a reviewable diff instead of leaving it possible with an untracked file.
    """
    try:
        import subprocess
        inside = subprocess.run(["git", "-C", root, "rev-parse", "--is-inside-work-tree"],
                                capture_output=True, text=True)
        if inside.returncode != 0 or inside.stdout.strip() != "true":
            return None, "%s is not a git work tree, so the tracked-file control DID NOT " \
                         "RUN here (stated, not silently skipped)" % root
        p = subprocess.run(["git", "-C", root, "ls-files", "--error-unmatch", rel],
                           capture_output=True, text=True)
        return (p.returncode == 0), ("tracked" if p.returncode == 0 else "UNTRACKED")
    except OSError as e:
        return None, "git unavailable (%s), so the tracked-file control DID NOT RUN" % e


def check_frozen(root, rec, digests):
    f, ln, _cat, _pin, detail, _why, pinned_sha = rec
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
    # T263 F-5: `produced:` used to be existence-only, so ANY existing path in the rig
    # satisfied it. Requiring the evidence to be PINNED closes the "swap it for
    # CAPTURE-PLAN.md" case only if CAPTURE-PLAN.md is unpinned -- it is not -- so this
    # is a floor, not a fix, and the provenance GRADE below is the honest part.
    if ev not in digests:
        return False, ("%s does not pin the evidence %s, so `produced:` names a file "
                       "nothing in this rig vouches for" % (MANIFEST_NAME, ev))
    actual = sha256(os.path.join(root, f))
    # ---- (a) THE DURABLE PIN. MANIFEST.sha256 is regenerated by `manifest.py write`,
    # which ANY worker runs as a matter of routine, so a death condition expressed only
    # against the manifest is undone by one ordinary command (T263 F-4, measured
    # end to end in ATTACK-REVIVE.txt). Field 7 pins the digest IN THE REGISTER ITSELF:
    # reviving a dead exemption then requires a SECOND, deliberate, reviewable edit to
    # this file, which `manifest.py write` cannot make.
    if pinned_sha and pinned_sha != "-":
        if actual != pinned_sha:
            return False, ("%s HAS BEEN EDITED (sha256 %s, THIS REGISTER pins %s) -- and "
                           "regenerating %s will NOT revive this exemption, because the "
                           "pin lives here, not there. A file being edited is not frozen: "
                           "add parse_float instead."
                           % (f, actual[:12], pinned_sha[:12], MANIFEST_NAME))
        durability = "register-pinned (survives `manifest.py write`)"
    else:
        durability = ("MANIFEST-ONLY -- WEAK: this record carries no register pin, so "
                      "`manifest.py write` REVIVES it after an edit")
    if actual != digests[f]:
        return False, ("%s HAS BEEN EDITED (sha256 %s, manifest pins %s) -- a file that is "
                       "being edited is not frozen, so add parse_float instead"
                       % (f, actual[:12], digests[f][:12]))
    tracked, tw = git_tracked(root, f)
    if tracked is False:
        return False, ("%s is UNTRACKED in git, so it produced no committed evidence and "
                       "cannot be T114-frozen. A record for an untracked file is how a "
                       "brand-new unguarded loader gets minted into this register."
                       % f)
    prov = "evidence NAMES its producer" if f in read_text(os.path.join(root, ev)) \
        else "ASSERTED ONLY -- the evidence does not name its producer, so this field is a " \
             "human claim the guard cannot verify"
    return True, ("frozen: sha256 matches %s; %s; produced %s; provenance: %s; git: %s"
                  % (MANIFEST_NAME, durability, ev, prov, tw))


def read_text(path):
    try:
        with open(path, "rb") as fh:
            return fh.read().decode("utf-8", "replace")
    except OSError:
        return ""


def check_reproduction(root, rec):
    f, ln, _cat, _pin, detail, _why, _sha = rec
    if not detail.startswith("reproduces:"):
        return False, "detail must be `reproduces:<path>:<line>`, got %r" % detail
    spec = detail[len("reproduces:"):].strip()
    tpath, _, tline = spec.rpartition(":")
    if not tpath or not tline.isdigit():
        return False, "cannot read `reproduces:<path>:<line>` out of %r" % spec
    tline = int(tline)
    # ---- (d) T263 F-6. An ABSOLUTE path was taken as given, so an untracked, deletable
    # file OUTSIDE THE REPOSITORY could license an in-tree unguarded money load, and the
    # licence silently changed meaning whenever that file changed. This is the one a
    # reviewer cannot audit, so it is refused outright -- and `..` is refused with it,
    # because it reaches the same place by a different spelling.
    if os.path.isabs(tpath):
        return False, ("`reproduces:` target %r is an ABSOLUTE path. A money guard may "
                       "not be licensed by a file outside the tree, which no reviewer "
                       "can see and anyone can delete. Name a repo-relative path."
                       % tpath)
    ap = os.path.join(root, tpath)
    real_root = os.path.realpath(root)
    real_ap = os.path.realpath(ap)
    if real_ap != real_root and not real_ap.startswith(real_root + os.sep):
        return False, ("`reproduces:` target %r escapes the root after realpath "
                       "normalisation (%s is not under %s). Same defect as an absolute "
                       "path, spelled with `..` or a symlink." % (tpath, real_ap, real_root))
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
        f, ln, cat, pinned, detail, reason, _frozen_sha = rec
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
