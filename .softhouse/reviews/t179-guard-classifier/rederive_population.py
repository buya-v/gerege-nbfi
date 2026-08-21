#!/usr/bin/env python3
"""T179 — re-derive the guarded/unguarded population from scratch, at a pinned commit,
with BOTH classifiers, and cross-tabulate them.

The task said: re-derive the number rather than inherit it, because inheriting a count
is exactly the failure mode under investigation.  So nothing here is taken from T156's
or T158's handoff:

  * the file list comes from `git ls-tree -r <ref>` — the tree, not the working copy,
    so a worker's uncommitted scratch cannot move the number;
  * T156's classifier is REBUILT BY PARSING T156's OWN SOURCE — `MUTATE`, `TARGETS`,
    `GUARD` and `SANDBOXY` are lifted out of its AST, never retyped;
  * the parser classifier is `guard_classify.py`, run over the same bytes;
  * every file is in exactly one bucket and the tallies are asserted to close.

Usage:  python3 rederive_population.py [--ref main] [--root .softhouse]
"""
import argparse
import ast
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import guard_classify as gc                                     # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
T156_SRC = os.path.join(REPO, ".softhouse", "capture", "pathb", "t149",
                        "t156-sweep-unguarded-mutators.py")


def literal_regexes(tree, varname):
    """Rebuild a `[(name, re.compile(lit)), ...]` list, or a bare re.compile(lit),
    from T156's own AST."""
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1 and
                isinstance(node.targets[0], ast.Name) and
                node.targets[0].id == varname):
            continue
        v = node.value
        if isinstance(v, ast.Call):                     # GUARD / SANDBOXY
            return [(varname, re.compile(v.args[0].value))]
        if isinstance(v, ast.List):                     # MUTATE / TARGETS
            out = []
            for elt in v.elts:
                nm = elt.elts[0].value
                rx = elt.elts[1].args[0].value
                out.append((nm, re.compile(rx)))
            return out
    raise SystemExit("could not lift %s out of %s — refusing to retype it"
                     % (varname, T156_SRC))


def t156_classifier():
    tree = ast.parse(open(T156_SRC, encoding="utf-8").read())
    return (literal_regexes(tree, "MUTATE"),
            literal_regexes(tree, "TARGETS"),
            literal_regexes(tree, "GUARD")[0][1],
            literal_regexes(tree, "SANDBOXY")[0][1])


def tree_files(ref, root):
    out = subprocess.run(["git", "-C", REPO, "ls-tree", "-r", "--name-only", ref,
                          "--", root], capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit("git ls-tree failed: %s" % out.stderr[:200])
    return [l for l in out.stdout.splitlines() if l]


_BLOB_CACHE = {}


def blob(ref, path):
    """Bytes of one blob, read once per (ref, path) and cached — a second `git show`
    per file made this script take minutes on ~500 files."""
    key = (ref, path)
    if key not in _BLOB_CACHE:
        p = subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (ref, path)],
                           capture_output=True)
        _BLOB_CACHE[key] = p.stdout if p.returncode == 0 else None
    return _BLOB_CACHE[key]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="main")
    ap.add_argument("--root", default=".softhouse")
    args = ap.parse_args()

    sha = subprocess.run(["git", "-C", REPO, "rev-parse", args.ref],
                         capture_output=True, text=True).stdout.strip()
    MUTATE, TARGETS, GUARD, SANDBOXY = t156_classifier()

    all_paths = tree_files(args.ref, args.root)
    scripts = [p for p in all_paths if p.endswith((".py", ".sh", ".bash"))]
    by_ext = {}
    for p in all_paths:
        if p.endswith((".py", ".sh", ".bash")):
            continue
        e = os.path.splitext(p)[1] or "<none>"
        by_ext[e] = by_ext.get(e, 0) + 1

    print("=== T179 — population re-derived, both classifiers, one pinned tree")
    print("ref                 : %s  (%s)" % (args.ref, sha))
    print("root                : %s" % args.root)
    print("enumerator          : git ls-tree -r (the TREE, not the working copy)")
    print("T156's regexes      : lifted from %s by ast, not retyped"
          % os.path.relpath(T156_SRC, REPO))
    print("shell parser        : %s"
          % (gc.SHELL_PARSER or "NONE — every .sh is REFUSED and counted"))
    print()

    print("--- DENOMINATORS")
    print("  files under %s at %s              : %d" % (args.root, args.ref[:12],
                                                        len(all_paths)))
    print("  of which scripts (.py/.sh/.bash)          : %d" % len(scripts))
    print("    .py                                     : %d"
          % len([p for p in scripts if p.endswith(".py")]))
    print("    .sh/.bash                               : %d"
          % len([p for p in scripts if not p.endswith(".py")]))
    print("  NON-script files, never inspected by either classifier: %d"
          % sum(by_ext.values()))
    print("    largest groups: %s"
          % ", ".join("%s %d" % (e, n)
                      for e, n in sorted(by_ext.items(), key=lambda t: -t[1])[:6]))
    print("  NOT SWEPT AT ALL: everything outside %s — nexus/, docs/, .claude/,"
          % args.root)
    print("    the repo root. Both classifiers share this blind spot.")
    print()

    if not scripts:
        sys.stderr.write("ERROR: zero files inspected — an error, not a pass (P-35)\n")
        return 3

    # ---- pass 1: T156's classifier, replicated exactly ------------------
    t156 = {}
    unreadable = []
    for rel in scripts:
        data = blob(args.ref, rel)
        if data is None:
            unreadable.append((rel, "git show failed"))
            continue
        try:
            src = data.decode("utf-8")
        except UnicodeDecodeError:
            unreadable.append((rel, "UnicodeDecodeError"))
            continue
        verbs = [n for n, rx in MUTATE if rx.search(src)]
        if not verbs:
            continue
        tgts = [n for n, rx in TARGETS if rx.search(src)]
        if not tgts:
            continue
        t156[rel] = {"verbs": verbs, "targets": tgts,
                     "guard": bool(GUARD.search(src)),
                     "sandboxy": bool(SANDBOXY.search(src))}

    hits = len(t156)
    guarded = [r for r, v in t156.items() if v["guard"]]
    unguarded = [r for r, v in t156.items() if not v["guard"]]
    print("--- T156's CLASSIFIER, replicated at this ref (file-level, source-text regex)")
    print("  hits (a mutation verb AND a trusted target anywhere in the file): %d"
          % hits)
    print("    scored GUARDED   : %d" % len(guarded))
    print("    scored UNGUARDED : %d" % len(unguarded))
    print("  unreadable         : %d" % len(unreadable))
    print("  [T158 recorded hits=130 guarded=19 unguarded=111 at ITS ref; this run is")
    print("   a different tree, so a difference here is drift, not a contradiction.]")
    print()

    # ---- pass 2: the parser -------------------------------------------
    results, refused = [], []
    for rel in scripts:
        data = blob(args.ref, rel)
        if data is None:
            continue
        try:
            src = data.decode("utf-8")
        except UnicodeDecodeError:
            refused.append((rel, gc.REFUSE_DECODE))
            continue
        if rel.endswith(".py"):
            res = gc.classify_python(rel, src)
        else:
            res = gc.classify_shell(rel, src)
        if res.get("refused"):
            refused.append((rel, res["refused"]))
        results.append(res)

    py_ok = [r for r in results if r["lang"] == "python" and not r["refused"]]
    matrix = {}
    for r in py_ok:
        for s in r["sites"]:
            matrix[(s["scope"], s["verdict"])] = matrix.get((s["scope"],
                                                             s["verdict"]), 0) + 1
    n_sites = sum(len(r["sites"]) for r in py_ok)

    print("--- THE PARSER, same bytes")
    print("  python files parsed                       : %d" % len(py_ok))
    print("  python files REFUSED (syntax/decode)      : %d"
          % len([1 for _r, why in refused if why != gc.REFUSE_SHELL]))
    print("  shell files REFUSED (no shell parser)     : %d"
          % len([1 for _r, why in refused if why == gc.REFUSE_SHELL]))
    print("  mutation call SITES in python             : %d" % n_sites)
    print()
    print("  scope x verdict (every site once):")
    hdr = "".join("%-26s" % v for v in gc.VERDICT_ORDER)
    print("    %-9s %s" % ("scope", hdr))
    for scope in (gc.TRUSTED, gc.UNKNOWN, gc.SCRATCH):
        row = [matrix.get((scope, v), 0) for v in gc.VERDICT_ORDER]
        print("    %-9s %s  (total %d)"
              % (scope, "".join("%-26d" % n for n in row), sum(row)))
    if sum(matrix.values()) != n_sites:
        print("    TALLY DOES NOT CLOSE — treat this run as broken")
    print()

    files_trusted_unguarded = sorted({r["path"] for r in py_ok for s in r["sites"]
                                      if s["scope"] == gc.TRUSTED and
                                      s["verdict"] == gc.UNGUARDED})
    files_unknown_unguarded = sorted({r["path"] for r in py_ok for s in r["sites"]
                                      if s["scope"] == gc.UNKNOWN and
                                      s["verdict"] == gc.UNGUARDED})
    print("  PYTHON files with >=1 UNGUARDED mutation of a TRUSTED artefact: %d"
          % len(files_trusted_unguarded))
    for f in files_trusted_unguarded:
        print("      %s" % f)
    print("  PYTHON files whose only unguarded sites have an UNRESOLVED target: %d"
          % len([f for f in files_unknown_unguarded
                 if f not in files_trusted_unguarded]))
    print()

    # ---- cross-tabulation ---------------------------------------------
    print("--- CROSS-TABULATION: where the two classifiers disagree")
    py_by_path = {r["path"]: r for r in py_ok}
    fp = []          # T156 GUARDED, parser says an unguarded trusted site exists
    fn = []          # T156 UNGUARDED, parser finds no unguarded site at all
    for rel in guarded:
        r = py_by_path.get(rel)
        if r is None:
            continue                      # shell: refused, counted below
        if any(s["verdict"] == gc.UNGUARDED and s["scope"] == gc.TRUSTED
               for s in r["sites"]):
            fp.append(rel)
    for rel in unguarded:
        r = py_by_path.get(rel)
        if r is None:
            continue
        if r["sites"] and not any(s["verdict"] == gc.UNGUARDED for s in r["sites"]):
            fn.append(rel)

    guarded_py = [r for r in guarded if r.endswith(".py")]
    guarded_sh = [r for r in guarded if not r.endswith(".py")]
    unguarded_py = [r for r in unguarded if r.endswith(".py")]
    unguarded_sh = [r for r in unguarded if not r.endswith(".py")]
    print("  T156 'GUARDED' hits: %d  (%d python, %d shell)"
          % (len(guarded), len(guarded_py), len(guarded_sh)))
    # The direct re-derivation of T158's "4 of 19 carry zero guards": for every
    # python file T156 scored GUARDED, count the guard NODES the parser can see.
    prose_only = []
    print("    every python 'GUARDED' file, with its real guard nodes:")
    for rel in sorted(guarded_py):
        r = py_by_path.get(rel)
        if r is None:
            continue
        print("      %-62s try/finally=%d live-handlers=%d restoring-CMs=%d  "
              "guard-words-in-string-literals=%d  mutation-sites=%d"
              % (rel, r.get("try_finally_nodes", 0), len(r.get("live_handlers", [])),
                 len(r.get("restoring_cms", [])), r.get("literal_guard_words", 0),
                 len(r["sites"])))
        if r.get("guard_nodes", 0) == 0:
            prose_only.append(rel)
    print("    -> python files T156 scored GUARDED with ZERO guard nodes of any "
          "kind: %d of %d" % (len(prose_only), len(guarded_py)))
    for rel in prose_only:
        print("         %s" % rel)
    print("    python ones the parser contradicts (unguarded trusted site): %d"
          % len(fp))
    for rel in sorted(fp):
        r = py_by_path[rel]
        bad = [s for s in r["sites"] if s["verdict"] == gc.UNGUARDED and
               s["scope"] == gc.TRUSTED]
        print("      %s  (%d unguarded trusted site(s), first at :%d, "
              "guard-words-in-string-literals=%d, try/finally nodes=%d)"
              % (rel, len(bad), bad[0]["line"], r.get("literal_guard_words", 0),
                 r.get("try_finally_nodes", 0)))
    print("    shell ones: %d — NOT adjudicated. No shell parser; refused, not "
          "assumed." % len(guarded_sh))
    print()
    print("  T156 'UNGUARDED' hits: %d  (%d python, %d shell)"
          % (len(unguarded), len(unguarded_py), len(unguarded_sh)))
    zero_sites = [rel for rel in sorted(unguarded_py)
                  if py_by_path.get(rel) is not None and
                  not py_by_path[rel]["sites"]]
    print("    python ones that perform NO MUTATION AT ALL by the parser: %d of %d"
          % (len(zero_sites), len(unguarded_py)))
    print("      (T156's hit criterion is 'a mutation verb matches ANYWHERE in the")
    print("       file' — including inside its own regex literals, docstrings and")
    print("       print() strings, so its hit set is not a set of mutators.)")
    for rel in zero_sites[:40]:
        print("         %s" % rel)
    print("    python ones the parser clears (no unguarded site at all): %d"
          % len(fn))
    for rel in sorted(fn)[:40]:
        print("      %s" % rel)
    print("    shell ones: %d — NOT adjudicated, for the same reason."
          % len(unguarded_sh))
    print()

    print("--- WHAT CAN HONESTLY BE SAID ABOUT THE POPULATION AT %s" % args.ref)
    print("  Adjudicable by a parser (python)        : %d files" % len(py_ok))
    print("  Not adjudicable here (shell, refused)   : %d files"
          % len([1 for _r, why in refused if why == gc.REFUSE_SHELL]))
    print("  Python files with a proven unguarded")
    print("    mutation of a trusted artefact        : %d" % len(files_trusted_unguarded))
    print("  Python files with an unguarded mutation")
    print("    of an UNRESOLVED target               : %d"
          % len([f for f in files_unknown_unguarded if f not in files_trusted_unguarded]))
    print("  A single 'the unguarded population is N' number is NOT derivable while")
    print("  the shell half is refused. Anyone quoting one is quoting a regex.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
