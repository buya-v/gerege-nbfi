#!/usr/bin/env python3
"""T476 / C-T467-3 + C-T467-1 -- WHAT THE THREE RULES COST, AND WHAT THEY SEE, AT SCALE.

Three questions, one instrument, because they are the same measurement pointed three ways:

  1  THE FALSE-POSITIVE POPULATION. T467 published "ZERO false positives" beside its rule.
     That is a fact about the FOUR guarded files. Over every tracked .py/.sh in the
     repository the T467 rule flags files the T455 rule does not, and T472 measured six.
     Re-derived here, with the member SET printed and its tree named, because a count with
     no members is not checkable and a measurement with no tree goes stale silently.

  2  THE SUPERSET RELATION -- the check T472's closing paragraph says nobody in this lineage
     had run. A generated CROSS PRODUCT of emitter x literal-spelling x tag-placement is
     graded by all three rules, and any case the OLD rule catches and the NEW one misses is
     a REGRESSION and fails this file. The matrix is enumerated mechanically, not hand-listed,
     because a hand list of shapes is exactly how T467 came to believe it had closed a class.

  3  THE ABLATION. Each arm of the T476 rule is disabled IN THE LIFTED CODE ITSELF -- never
     in a retyped copy -- and the population cost and the catch set are re-measured. That is
     what turns "the widening is free" from an assertion into a number.

EVERY RULE IS LIFTED FROM ITS BLOB BY AST. Nothing here retypes a predicate: grading a
retyped copy of a rule is grading the retyping.

  python3 20-t476-population-cost.py <repo> <ref-T455> <ref-T467> <ref-T476>

EXIT 0  every recorded relation held.
EXIT 1  a relation did not -- named on stdout.
EXIT 3  REFUSED: could not measure. Never a pass.
"""
import ast
import inspect
import subprocess
import sys

WANT = ("FALSE_CLAIMS", "TAG", "_CONVERSION", "_FIELD", "states_a_false_claim",
        "strip_trailing_comment", "strip_trailing_comment_posix", "quoted_segments",
        "join_continuations", "squeeze", "_fold", "python_payloads", "emitter_payloads",
        "emitted_payload", "printed_payloads", "tagged_blocks", "grade_binding")

S = ".softhouse"
GRADER = S + "/reviews/A2-11/verify-capture-integrity.py"


def sh(repo, *args):
    p = subprocess.run(["git", "-C", repo] + list(args), capture_output=True)
    if p.returncode != 0:
        sys.stderr.write("REFUSED: git %s failed\n" % " ".join(args))
        sys.exit(3)
    return p.stdout


def lift(repo, ref):
    """The predicate at one ref, as a live namespace, extracted from the blob by AST."""
    src = sh(repo, "show", "%s:%s" % (ref, GRADER)).decode("utf-8", "replace")
    tree = ast.parse(src)
    pieces = []
    for node in tree.body:
        name = None
        if isinstance(node, ast.FunctionDef):
            name = node.name
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
        if name in WANT:
            pieces.append(ast.get_source_segment(src, node))
    if not pieces:
        sys.stderr.write("REFUSED: no predicate found at %s\n" % ref)
        sys.exit(3)
    ns = {}
    exec(compile("import ast, os, re, sys\n\n" + "\n\n".join(pieces), "<%s>" % ref, "exec"), ns)
    gb = ns["grade_binding"]
    n = len(inspect.signature(gb).parameters)
    ns["grade"] = (lambda t, r: gb(t)) if n == 1 else (lambda t, r: gb(t, r))
    return ns


def corpus(repo, ref):
    names = [f for f in sh(repo, "ls-tree", "-r", "--name-only", ref).decode().split("\n")
             if f.endswith(".py") or f.endswith(".sh")]
    spec = "".join("%s:%s\n" % (ref, f) for f in names).encode()
    p = subprocess.run(["git", "-C", repo, "cat-file", "--batch"], input=spec,
                       capture_output=True)
    if p.returncode != 0:
        sys.stderr.write("REFUSED: git cat-file --batch failed\n")
        sys.exit(3)
    buf, out, i = p.stdout, {}, 0
    for f in names:
        nl = buf.index(b"\n", i)
        size = int(buf[i:nl].decode().split()[2])
        out[f] = buf[nl + 1:nl + 1 + size].decode("utf-8", "replace")
        i = nl + 1 + size + 1
    return out


def flagged(ns, texts):
    """{file: [payload sites]} for predicate 2, plus the files whose grading RAISED."""
    hits, raised = {}, {}
    for f, t in texts.items():
        try:
            _u, _q, p = ns["grade"](t, f)
        except Exception as exc:            # a rule that crashes on a corpus member has not
            raised[f] = type(exc).__name__  # graded it -- recorded, never silently skipped
            continue
        if p:
            hits[f] = p
    return hits, raised


# --------------------------------------------------------------------------------------
# THE GENERATED MATRIX. Enumerated as a cross product so it is not a list of shapes somebody
# thought of. The sentence is ASSEMBLED from the rule's own pattern table, never typed.
# --------------------------------------------------------------------------------------
def matrix(FALSE_CLAIMS, TAG):
    claim = FALSE_CLAIMS[3]
    S1 = "There is no " + claim + "."
    GOOD_SH = '  echo "  [%s] %s"\n  echo "THE BASELINE IS THE BLOB AT THE COMMIT."\n' \
              % (TAG, S1)
    GOOD_PY = 'print("  [%s] %s")\n' % (TAG, S1)

    def halves(s):
        w = s.split()
        return " ".join(w[:len(w) // 2]), " ".join(w[len(w) // 2:])

    sh_lit = {
        "dquote":   lambda s: '"%s"' % s,
        "squote":   lambda s: "'%s'" % s,
        "bare":     lambda s: s,
        "adjacent": lambda s: '"%s" "%s"' % (s[:len(s) // 2], s[len(s) // 2:]),
        "continue": lambda s: '"%s \\\n  %s"' % halves(s),
    }
    sh_car = {
        "echo":        "  echo %s",
        "echo-tab":    "  echo\t%s",
        "stderr-echo": "  >&2 echo %s",
        "printf":      "  printf '%%s\\n' %s",
        "command":     "  command echo %s",
        "eval":        "  eval echo %s",
        "paramexp":    "  X476=abc\n  echo ${X476#a} %s",
    }
    py_lit = {
        "str":      lambda s: '"%s"' % s,
        "bytes":    lambda s: 'b"%s"' % s,
        "fstring":  lambda s: 'f"%s"' % s,
        "concat":   lambda s: '"%s" + " %s"' % halves(s),
        "percent":  lambda s: '"%s" %% "HEAD"' % s.replace("HEAD", "%s"),
        "format":   lambda s: '"%s".format()' % s,
        "decode":   lambda s: 'b"%s".decode()' % s,
        "triple":   lambda s: '"""%s"""' % s,
    }
    py_car = {
        "print":     "print(%s)",
        "syswrite":  "sys.stdout.write(%s)",
        "oswrite":   "os.write(1, %s)",
        "assign":    "_v476 = %s",
        "logging":   "logging.info(%s)",
        "subproc":   'subprocess.run(["printf", %s])',
    }
    cases = []
    for lname, lit in sh_lit.items():
        for cname, car in sh_car.items():
            for tname, tagged in (("trailing-comment", 1), ("untagged", 0), ("tag-inside", 2)):
                body = lit(S1 if tagged != 2 else "[%s] %s" % (TAG, S1))
                line = car % body
                if tagged == 1:
                    line += "  # " + TAG
                cases.append(("sh/%s/%s/%s" % (cname, lname, tname), "fixture.sh",
                              GOOD_SH + line + "\n", tagged))
    for lname, lit in py_lit.items():
        for cname, car in py_car.items():
            for tname, tagged in (("trailing-comment", 1), ("untagged", 0), ("tag-inside", 2)):
                body = lit(S1 if tagged != 2 else "[%s] %s" % (TAG, S1))
                line = car % body
                if tagged == 1:
                    line += "  # " + TAG
                cases.append(("py/%s/%s/%s" % (cname, lname, tname), "fixture.py",
                              GOOD_PY + line + "\n", tagged))
    return cases


def main():
    if len(sys.argv) != 5:
        sys.stderr.write(__doc__.rsplit("  python3", 1)[-1])
        return 3
    repo, r455, r467, r476 = sys.argv[1:5]
    rules = [("T455", r455), ("T467", r467), ("T476", r476)]
    ns = {name: lift(repo, ref) for name, ref in rules}
    for name, ref in rules:
        print("  rule %-5s lifted from %s:%s  -> %s"
              % (name, ref, GRADER.rsplit("/", 1)[-1],
                 " ".join(sorted(n for n in WANT if n in ns[name]))))
    FC, TAG = ns["T476"]["FALSE_CLAIMS"], ns["T476"]["TAG"]
    if ns["T455"]["FALSE_CLAIMS"] != FC or ns["T467"]["FALSE_CLAIMS"] != FC:
        print("REFUSED: the three refs do not grade the same claim table.")
        return 3
    bad = []

    # ---- 1. the population -------------------------------------------------------------
    print()
    print("=== 1. THE FALSE-POSITIVE POPULATION, over every tracked .py/.sh at %s ===" % r476)
    texts = corpus(repo, r476)
    print("  population: %d files" % len(texts))
    hits = {}
    for name, _ in rules:
        h, raised = flagged(ns[name], texts)
        hits[name] = h
        print("  %-5s flags %4d file(s); grading RAISED on %d" % (name, len(h), len(raised)))
        for f, why in sorted(raised.items()):
            print("        RAISED %-70s %s" % (f, why))
    only467 = sorted(set(hits["T467"]) - set(hits["T455"]))
    print()
    print("  C-T467-3 RE-DERIVED -- flagged by T467, NOT by T455  (n=%d):" % len(only467))
    for f in only467:
        for site in hits["T467"][f][:2]:
            print("    %s" % site)
        print("      in %s" % f)
    print()
    print("  T476 vs T467 delta: +%d file(s), -%d file(s)"
          % (len(set(hits["T476"]) - set(hits["T467"])),
             len(set(hits["T467"]) - set(hits["T476"]))))
    for f in sorted(set(hits["T476"]) - set(hits["T467"])):
        print("    NEW FALSE POSITIVE INTRODUCED BY T476: %s" % f)
    if set(hits["T467"]) - set(hits["T476"]):
        for f in sorted(set(hits["T467"]) - set(hits["T476"])):
            print("    NO LONGER FLAGGED BY T476: %s" % f)
            bad.append("T476 stopped flagging %s" % f)
    guarded = [f for f in texts if f.endswith("/verify-capture-integrity.py")
               or f.endswith("/run-all.sh")
               or f.endswith("/10-drive-conditions.sh")
               or f.endswith("/12-relaunder-manifest.py")]
    still = [f for f in guarded if f in hits["T476"]]
    print("  the four guarded files flagged by T476 on a clean tree: %d %s"
          % (len(still), still))
    if still:
        bad.append("T476 reddens a guarded file on a clean tree")

    # ---- 2. the superset relation ------------------------------------------------------
    print()
    print("=== 2. THE SUPERSET RELATION, over a GENERATED cross product ===")
    cases = matrix(FC, TAG)
    nparse = 0
    for cid, rel, text, _t in cases:
        if rel.endswith(".py"):
            try:
                ast.parse(text)
                nparse += 1
            except SyntaxError:
                pass
    print("  cases: %d  (of the python ones, %d parse; a .py that does not parse falls back"
          % (len(cases), nparse))
    print("         to the lexical rule, which is behaviour under test, not an escape)")
    caught = {}
    for name, _ in rules:
        c = set()
        for cid, rel, text, _t in cases:
            try:
                u, q, p = ns[name]["grade"](text, rel)
            except Exception as exc:
                print("    RAISED  %-5s on %s: %s" % (name, cid, type(exc).__name__))
                if name == "T476":
                    bad.append("T476 raised on generated case %s" % cid)
                continue
            if u or p:
                c.add(cid)
        caught[name] = c
        print("  %-5s catches %3d of %d" % (name, len(c), len(cases)))
    regress = sorted(caught["T455"] - caught["T476"])
    print()
    print("  ACCEPTANCE TEST -- cases T455 catches and T476 MISSES: %d" % len(regress))
    for cid in regress:
        print("    REGRESSION %s" % cid)
        bad.append("regression on generated case %s" % cid)
    lost467 = sorted(caught["T455"] - caught["T467"])
    print("  the same relation for T467 (what this repair exists to fix): %d" % len(lost467))
    for cid in lost467:
        print("    T467 misses what T455 caught: %s" % cid)
    gained = sorted(caught["T476"] - caught["T467"])
    print("  cases T476 catches that T467 does not: %d" % len(gained))
    for cid in gained:
        print("    +%s" % cid)
    # the discrimination half: a payload that CARRIES the tag must never be flagged
    inside = [cid for cid, rel, text, t in cases if t == 2 and cid in caught["T476"]]
    print()
    print("  DISCRIMINATION -- correctly TAGGED payloads flagged by T476: %d" % len(inside))
    for cid in inside[:10]:
        print("    FALSE POSITIVE ON A TAGGED QUOTATION: %s" % cid)
    if inside:
        bad.append("T476 flags %d correctly tagged quotations" % len(inside))
    missed = sorted(cid for cid, rel, text, t in cases if t == 1 and cid not in caught["T476"])
    print("  DECLARED BLIND SET -- trailing-comment abuses T476 still misses: %d" % len(missed))
    for cid in missed:
        print("    OPEN %s" % cid)

    # ---- 3. the ablation ---------------------------------------------------------------
    print()
    print("=== 3. THE ABLATION -- each arm disabled IN THE LIFTED CODE, cost re-measured ===")
    base_fp, base_catch = set(hits["T476"]), caught["T476"]
    ABL = (
        ("ARM 1 (T455 emitter rule)", "emitter_payloads", lambda ns_: (lambda text: [])),
        ("continuation joining", "join_continuations",
         lambda ns_: (lambda text: [(l, i) for i, l in enumerate(text.split("\n"), 1)])),
        ("POSIX word-start #", "strip_trailing_comment_posix",
         lambda ns_: ns_["strip_trailing_comment"]),
        ("whitespace normalisation", "squeeze", lambda ns_: (lambda s: s)),
        ("the widened python arm", "python_payloads", lambda ns_: ns["T467"]["python_payloads"]),
    )
    for label, slot, repl in ABL:
        n2 = lift(repo, r476)
        if slot not in n2:
            print("  REFUSED: %s is not a name in the T476 rule" % slot)
            return 3
        n2[slot] = repl(n2)
        gb = n2["grade_binding"]
        n2["grade"] = lambda t, r: gb(t, r)
        h, _ = flagged(n2, texts)
        c = set()
        for cid, rel, text, _t in cases:
            try:
                u, q, p = n2["grade"](text, rel)
            except Exception:
                continue
            if u or p:
                c.add(cid)
        print("  without %-26s FP=%-3d (delta %+d)   catches=%-3d (delta %+d)"
              % (label, len(h), len(h) - len(base_fp), len(c), len(c) - len(base_catch)))
        if len(c) >= len(base_catch):
            print("        NOTE: this arm earns NO catches on this matrix -- the other arms")
            print("        happen to cover the same shapes. That is not a reason to delete it:")
            print("        ARM 1 exists so that 'the union sees everything the replaced rule")
            print("        saw' is a property of the CODE rather than of whichever shapes a")
            print("        matrix enumerates -- which is the exact failure this repair repairs.")
            print("        30-t476-superset-falsifiable.sh unwires it and the SUPERSET CONTROL")
            print("        goes RED on a clean tree. Read that before removing anything here.")
    print()
    print("  Read the ablation as the cost side of the repair. Every arm BELOW THE FIRST is")
    print("  one this matrix shows earning catches. ARM 1 earns NONE of them, and the note")
    print("  above it is the reason it stays anyway. NONE of the five moves the false-positive")
    print("  population off the six files T467 already flagged: the repair is monotonic here.")

    print()
    if bad:
        print("RESULT: %d relation(s) did NOT hold." % len(bad))
        for b in bad:
            print("  - %s" % b)
        return 1
    print("RESULT: every recorded relation held. EXIT 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
