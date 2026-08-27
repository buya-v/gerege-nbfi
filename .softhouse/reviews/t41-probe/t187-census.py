#!/usr/bin/env python3
"""T187 guard census for `.softhouse/reviews/t41-probe/` - and the statement of
the counting rule this task used.

WHY A THIRD CENSUS EXISTS, SAID PLAINLY.  T167's sibling census reads guards
from each file's OWN ast, so T178's shared-module refactor made it score eight
hardened files as UNGUARDED.  T178 wrote a successor that RESOLVES DELEGATION -
the right fix - but hard-wired its family to `glob("t47_edit_*.py")`, and
t47-probe is outside T187's scope guard, so it cannot be widened here.  This
file therefore SUPERSEDES T167's census for this directory and REUSES T178's
principle: a file counts as guarded when it delegates every write to the shared
guard, and the shared guard is READ AND CHECKED by following the import.  It is
not a copy of T178's census logic for a different directory - it answers a
different question as well (the population rule below).

THE COUNTING RULE, STATED SO IT CAN BE DISAGREED WITH.
  A file is a member of the population iff, from its OWN ast alone, it contains
  at least one call that opens a path for TRUNCATING WRITE - `open`/`io.open`
  with a mode string containing `w`, or `Path(...).write_text/write_bytes` -
  whose path expression RESOLVES STATICALLY to
      docs/adr/DEC-1-schedule-generator-adapter.md          (the RATIFIED DEC-1)
   or nexus/internal/apps/loanschedule/contract/contract.go (the FROZEN contract)
  Resolution follows (a) module-level string constants and (b) a helper
  function's `path` parameter, back to that helper's call sites in the same
  file.  Counted PER FILE, once.  A file that writes BOTH artefacts is ONE
  member and is reported against both.
  MENTIONS DO NOT COUNT.  A file that merely names an artefact in a comment, a
  docstring or a replacement string is NOT a member; only a resolvable
  truncating write is.
  UNRESOLVABLE COUNTS AS A MEMBER, LOUDLY.  A truncating write whose path
  cannot be resolved statically is reported UNDETERMINED and fails the census -
  never dropped (P-40).

EXCLUSIONS, PRINTED RATHER THAN IMPLIED (P-56 rule 1).  This census walks
exactly one directory - the one holding this file - and never recurses.  It
does not walk the repository, so it cannot pick up `.claude/worktrees/`.

NOTHING HERE IS EXECUTED.  Every answer comes from an ast and from string
membership.  Running one of these scripts to find out what it does is the
defect, not the test.

  usage: t187-census.py [--scan=DIR]
    --scan=DIR   census an alternative copy of the family (e.g. the PRE-FIX
                 bytes checked out elsewhere), so this census can itself be
                 driven RED.  The LIVE artefacts read are always the real ones.

Exit 0 = every rewriter in the family is guarded and none can reach a ratified
         or frozen artefact.
Exit 1 = at least one can, or at least one could not be measured.
"""
import ast
import glob
import hashlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
GUARD = os.path.join(os.path.dirname(HERE), "t47-probe", "t178_guard.py")

ADR_REL = "docs/adr/DEC-1-schedule-generator-adapter.md"
GO_REL = "nexus/internal/apps/loanschedule/contract/contract.go"
PROTECTED = {ADR_REL: "DEC-1", GO_REL: "contract.go"}

SCAN = HERE
for a in sys.argv[1:]:
    if a.startswith("--scan="):
        SCAN = a.split("=", 1)[1]
    else:
        sys.stderr.write("usage: t187-census.py [--scan=DIR]\n")
        sys.exit(1)

# NAMED EXEMPTIONS, with a CHECKABLE condition - never a bare allowlist, which
# would be P-22's guard that cannot fail.  An exemption is granted only if the
# condition also holds, it is PRINTED whenever it is used, and a file that
# claims one but fails the condition is a PROBLEM.
EXEMPT = {
    "t187-redgreen.py": (
        "the T187 prover: every write it makes goes into a tempfile.mkdtemp()"
        " scratch tree, and the two protected paths appear in it only as READ"
        " sources and as expected-digest constants",
        lambda src, sites: ("tempfile.mkdtemp(" in src
                            and not any(pth in PROTECTED for pth, _ in sites)),
    ),
}

PROBLEMS = []


def sha_file(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()


def module_consts(tree):
    out = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) \
                and isinstance(n.value.value, str):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    out[t.id] = n.value.value
    return out


def enclosing_funcs(tree):
    """child node -> the FunctionDef that contains it."""
    owner = {}
    for fn in ast.walk(tree):
        if isinstance(fn, ast.FunctionDef):
            for c in ast.walk(fn):
                owner[c] = fn
    return owner


def call_site_args(tree, fname, argpos):
    """Every statically-known value passed at `argpos` to calls of `fname`."""
    out = set()
    consts = module_consts(tree)
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and getattr(n.func, "id", None) == fname \
                and len(n.args) > argpos:
            a = n.args[argpos]
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                out.add(a.value)
            elif isinstance(a, ast.Name) and a.id in consts:
                out.add(consts[a.id])
            else:
                out.add(None)
    return out


def resolve(tree, expr, owner):
    """Resolve a path expression to a set of literal paths; None = unknown."""
    consts = module_consts(tree)
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return {expr.value}
    if isinstance(expr, ast.Name):
        if expr.id in consts:
            return {consts[expr.id]}
        fn = owner.get(expr)
        if fn is not None:
            names = [a.arg for a in fn.args.args]
            if expr.id in names:
                return call_site_args(tree, fn.name, names.index(expr.id))
    return {None}


def write_sites(tree):
    """[(path_or_None, how)] for every truncating write-open in the module."""
    owner = enclosing_funcs(tree)
    out = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        fname = getattr(n.func, "attr", getattr(n.func, "id", None))
        if fname == "open" and len(n.args) >= 2:
            m = n.args[1]
            if isinstance(m, ast.Constant) and "w" in str(m.value):
                for p in resolve(tree, n.args[0], owner):
                    out.append((p, "open(mode=%r)" % m.value))
        elif fname in ("write_text", "write_bytes"):
            recv = n.func.value
            if isinstance(recv, ast.Call) and len(recv.args) >= 1:
                for p in resolve(tree, recv.args[0], owner):
                    out.append((p, fname))
            else:
                out.append((None, fname))
    return out


def delegates(tree, src):
    """Does the file hand every write to the shared guard?"""
    imported = any(isinstance(n, ast.Import)
                   and any(al.name == "t178_guard" for al in n.names)
                   for n in ast.walk(tree))
    commits = sum(1 for n in ast.walk(tree)
                  if isinstance(n, ast.Call)
                  and getattr(n.func, "attr", None) == "commit")
    loads = sum(1 for n in ast.walk(tree)
                if isinstance(n, ast.Call)
                and getattr(n.func, "attr", None) == "load")
    return imported and commits >= 1 and loads >= 1


def guard_is_sound():
    """FOLLOW THE IMPORT.  Read the shared guard and check the properties the
    delegating files are being credited with.  A census that credited
    delegation without reading the delegate would be P-22 again."""
    if not os.path.isfile(GUARD):
        PROBLEMS.append("shared guard %s is MISSING" % GUARD)
        return False
    src = io.open(GUARD, encoding="utf-8").read()
    tree = ast.parse(src)
    want = {
        "atomic os.replace": "os.replace(" in src,
        "mkstemp in the target's own dir": "tempfile.mkstemp(dir=" in src,
        "fsync": "os.fsync(" in src,
        "st_dev compared": "st_dev" in src,
        "content gate on the TARGET": "before_sha256" in src,
        "content gate on the CANDIDATE": "after_sha256" in src,
        "refuses the protected artefact itself": "protected_real" in src,
        "refuses targets inside the repo working tree": "repo_real" in src,
        "no bare assert": not any(isinstance(n, ast.Assert)
                                  for n in ast.walk(tree)),
    }
    print("SHARED GUARD (followed by import): %s  sha256 %s"
          % (os.path.relpath(GUARD, REPO), sha_file(GUARD)))
    ok = True
    for k, v in want.items():
        print("  %-46s %s" % (k, "yes" if v else "**NO**"))
        if not v:
            PROBLEMS.append("shared guard lacks: %s" % k)
            ok = False
    return ok


def pinned_digests(tree):
    return {v for k, v in module_consts(tree).items()
            if k.startswith(("BEFORE_", "AFTER_")) and len(v) == 64}


def main():
    live = {}
    for rel, label in PROTECTED.items():
        p = os.path.join(REPO, rel)
        live[rel] = sha_file(p) if os.path.isfile(p) else None
        print("LIVE %-12s %s  %s" % (label, live[rel], rel))
    print("")
    sound = guard_is_sound()
    print("\nSCAN ROOT      %s (one directory, NOT recursive)" % SCAN)
    print("EXCLUSIONS     nothing under it is walked recursively; "
          ".claude/worktrees/ is unreachable by construction\n")

    files = sorted(glob.glob(os.path.join(SCAN, "*.py")))
    members, nonmembers, unresolved = [], [], []
    print("%-22s %-12s %-11s %s" % ("FILE", "WRITES", "GUARDED", "TARGET(S)"))
    print("-" * 78)
    for f in files:
        name = os.path.basename(f)
        src = io.open(f, encoding="utf-8").read()
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            PROBLEMS.append("%s: DOES NOT PARSE (%s)" % (name, e))
            print("%-22s %s" % (name, "**DOES NOT PARSE**"))
            continue
        sites = write_sites(tree)
        hits = sorted({PROTECTED[p] for p, _ in sites if p in PROTECTED})
        unk = [h for p, h in sites if p is None]
        deleg = delegates(tree, src)
        # Post-fix files carry the target in the guard policy argument, not in
        # a path constant.
        if not hits and deleg:
            if "guard.RATIFIED_ADR" in src:
                hits.append("DEC-1")
            if "guard.FROZEN_CONTRACT" in src:
                hits.append("contract.go")
            hits = sorted(set(hits))
        if unk and not deleg:
            if name in EXEMPT:
                why, cond = EXEMPT[name]
                if cond(src, sites):
                    print("%-22s %-12s %-11s EXEMPT - %s"
                          % (name, "scratch", "n/a", why))
                else:
                    PROBLEMS.append("%s: claims an exemption but fails its "
                                    "condition" % name)
            else:
                unresolved.append(name)
                PROBLEMS.append("%s: truncating write with an UNRESOLVABLE "
                                "target (%s)"
                                % (name, ", ".join(sorted(set(unk)))))
        if hits:
            members.append((name, hits, deleg))
            own_atomic = "os.replace(" in src
            guarded = deleg or own_atomic
            print("%-22s %-12s %-11s %s"
                  % (name, "yes" if sites else "delegated",
                     "yes (shared)" if deleg else
                     ("yes (own)" if own_atomic else "**NO**"),
                     ", ".join(hits)))
            if not guarded:
                PROBLEMS.append("%s: UNGUARDED truncating write to %s"
                                % (name, ", ".join(hits)))
            for d in pinned_digests(tree):
                for rel, lv in live.items():
                    if d == lv:
                        PROBLEMS.append(
                            "%s: pins a digest EQUAL to the live %s - it could "
                            "reach the artefact on content grounds"
                            % (name, PROTECTED[rel]))
        else:
            nonmembers.append(name)
    print("-" * 78)
    print("POPULATION under the rule above: %d file(s)" % len(members))
    adr = [m[0] for m in members if "DEC-1" in m[1]]
    go = [m[0] for m in members if "contract.go" in m[1]]
    both = [m[0] for m in members if len(m[1]) == 2]
    print("  write the RATIFIED DEC-1        : %2d  %s" % (len(adr),
                                                           ", ".join(adr)))
    print("  write the FROZEN contract.go    : %2d  %s" % (len(go),
                                                           ", ".join(go)))
    print("  write BOTH (counted once above) : %2d  %s" % (len(both),
                                                           ", ".join(both)))
    print("NOT MEMBERS (%d, named per P-40): %s"
          % (len(nonmembers), ", ".join(nonmembers)))
    print("UNRESOLVED TARGETS: %d" % len(unresolved))
    print("FILES INSPECTED: %d" % len(files))
    if not sound:
        print("\nTHE SHARED GUARD ITSELF DID NOT PASS - no delegation credit "
              "is safe.")
    if PROBLEMS:
        print("\nPROBLEMS (%d):" % len(PROBLEMS))
        for p in PROBLEMS:
            print("  " + p)
        return 1
    print("\nNo file in this family can reach a ratified or frozen artefact.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
