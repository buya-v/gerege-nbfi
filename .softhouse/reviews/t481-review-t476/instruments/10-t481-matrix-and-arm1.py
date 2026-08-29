#!/usr/bin/env python3
"""T481 -- THE SUPERSET RELATION AND THE LOAD-BEARINGNESS OF ARM 1, RE-DERIVED.

Written for T481's review of T476. Nothing here is inherited: every rule is LIFTED FROM ITS
OWN BLOB by AST (grading a retyped copy of a rule is grading the retyping), and the cross
product below is MY enumeration, not T476's -- with axes T476's generator does not have,
because a population that cannot express a defect cannot catch it.

WHAT THIS MEASURES

  1  THE SUPERSET RELATION, over a cross product with 6 tag placements (T476 has 3),
     10 shell literal spellings (T476 has 5), 11 python literal spellings (T476 has 8),
     11 python carriers (T476 has 6), 9 shell carriers (T476 has 7), and a FILE-TYPE axis
     T476 does not have at all (a .py that does NOT parse -> the lexical fallback).
     ACCEPTANCE: no case T455 catches may be missed by T476.

  2  THE DISCRIMINATION HALF, which is where the risk actually is once the union is proved
     monotonic: a case whose tag IS printed must NOT be flagged. T476 reports 0 over its own
     249; this asks the same question over placements it does not enumerate.

  3  IS ARM 1 LOAD-BEARING? For every case, the union is re-graded with ARM 1 unwired IN THE
     LIFTED CODE. A case that changes is a case ARM 1 decides. The answer is reported split
     by whether the decided case is a CATCH (ARM 1 earns its keep) or a FALSE POSITIVE (ARM 1
     costs).

  4  ARM 1 vs ARM 3 AS SETS, on shell text -- whether ARM 1's payloads are literally a subset
     of ARM 3's for a non-continued line, which is what decides whether the SUPERSET CONTROL
     can fail at all on shell fixtures.

NO REPO-RELATIVE PATH IS SPELLED AS A LITERAL (P-103): the grader's path is assembled from
S at run time, and the repo and refs are REQUIRED arguments with no defaults.

  python3 10-t481-matrix-and-arm1.py <repo> <ref-T455> <ref-T467> <ref-T476>

EXIT 0  every recorded relation held.
EXIT 1  a relation did not -- named on stdout.
EXIT 3  REFUSED: could not measure. Never a pass.
"""
import ast
import inspect
import subprocess
import sys

S = ".softhouse"
GRADER = S + "/reviews/A2-11/verify-capture-integrity.py"

WANT = ("FALSE_CLAIMS", "TAG", "_CONVERSION", "_FIELD", "states_a_false_claim",
        "strip_trailing_comment", "strip_trailing_comment_posix", "quoted_segments",
        "join_continuations", "squeeze", "_fold", "python_payloads", "emitter_payloads",
        "emitted_payload", "printed_payloads", "tagged_blocks", "grade_binding")


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo] + list(args), capture_output=True)
    if p.returncode != 0:
        sys.stderr.write("REFUSED: git %s failed: %s\n"
                         % (" ".join(args), p.stderr.decode("utf-8", "replace")[:300]))
        sys.exit(3)
    return p.stdout


def lift(repo, ref):
    """The predicate at one ref as a live namespace, taken from the blob, never retyped."""
    src = git(repo, "show", "%s:%s" % (ref, GRADER)).decode("utf-8", "replace")
    pieces, seen = [], []
    tree = ast.parse(src)
    for node in tree.body:
        name = None
        if isinstance(node, ast.FunctionDef):
            name = node.name
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
        if name in WANT:
            pieces.append(ast.get_source_segment(src, node))
            seen.append(name)
    if "grade_binding" not in seen:
        sys.stderr.write("REFUSED: no grade_binding at %s\n" % ref)
        sys.exit(3)
    ns = {}
    exec(compile("import ast, os, re, sys\n\n" + "\n\n".join(pieces), "<%s>" % ref, "exec"), ns)
    gb = ns["grade_binding"]
    n = len(inspect.signature(gb).parameters)
    ns["_names"] = seen
    ns["grade"] = (lambda t, r: gb(t)) if n == 1 else (lambda t, r: gb(t, r))
    return ns


# ---------------------------------------------------------------------------------------
# THE CROSS PRODUCT. Assembled from the rule's OWN claim table, never typed, so this file is
# not itself an untagged assertion of the sentence it grades.
# ---------------------------------------------------------------------------------------
def matrix(FALSE_CLAIMS, TAG):
    claim = FALSE_CLAIMS[3]
    S1 = "There is no " + claim + "."
    def _h(s):
        """The two halves OF THE STRING PASSED IN, never of a precomputed sentence.

        MY FIRST RUN OF THIS FILE COMPUTED THE HALVES ONCE, from the untagged sentence, so
        every splitting spelling silently DROPPED the tag its placement had just inserted and
        the file reported 44 "tagged payloads wrongly flagged" that were not tagged payloads
        at all. A case that measures the wrong thing must not be able to report a number.
        Repaired at the instrument, and recorded here rather than quietly corrected.
        """
        w = s.split()
        return " ".join(w[:len(w) // 2]), " ".join(w[len(w) // 2:])
    GOOD_SH = ('  echo "  [%s] %s"\n'
               '  echo "THE BASELINE IS THE BLOB AT THE COMMIT."\n' % (TAG, S1))
    GOOD_PY = 'print("  [%s] %s")\n' % (TAG, S1)

    # ---- literal spellings -------------------------------------------------------------
    sh_lit = {
        "dquote":    lambda s: '"%s"' % s,
        "squote":    lambda s: "'%s'" % s,
        "bare":      lambda s: s,
        "adjacent":  lambda s: '"%s" "%s"' % (s[:len(s) // 2], s[len(s) // 2:]),
        "continue":  lambda s: '"%s \\\n  %s"' % _h(s),
        # --- T481 additions, none of them in T476's enumeration ---
        "ansic":     lambda s: "$'%s'" % s,
        "escaped":   lambda s: s.replace(" ", "\\ "),
        "mixed":     lambda s: '"%s"\'%s\'' % (s[:len(s) // 2], s[len(s) // 2:]),
        "wordsplit": lambda s: '"%s " "%s"' % (" ".join(s.split()[:-1]), s.split()[-1]),
        "varhalf":   lambda s: 'P481="%s"; echo "$P481 %s"; :' % _h(s),
    }
    sh_car = {
        "echo":        "  echo %s",
        "echo-tab":    "  echo\t%s",
        "stderr-echo": "  >&2 echo %s",
        "printf":      "  printf '%%s\\n' %s",
        "command":     "  command echo %s",
        "eval":        "  eval echo %s",
        "paramexp":    "  X481=abc\n  echo ${X481#a} %s",
        # --- T481 additions ---
        "heredoc":     "  cat <<'E481'\n%s\nE481",
        "tee":         "  echo %s | tee -a /dev/null",
    }
    py_lit = {
        "str":       lambda s: '"%s"' % s,
        "bytes":     lambda s: 'b"%s"' % s,
        "fstring":   lambda s: 'f"%s"' % s,
        "concat":    lambda s: '"%s" + " %s"' % _h(s),
        "percent":   lambda s: '"%s" %% "HEAD"' % s.replace("HEAD", "%s"),
        "format":    lambda s: '"%s".format()' % s,
        "decode":    lambda s: 'b"%s".decode()' % s,
        "triple":    lambda s: '"""%s"""' % s,
        # --- T481 additions ---
        "implicit":  lambda s: '"%s " "%s"' % _h(s),
        "join":      lambda s: '" ".join(["%s", "%s"])' % _h(s),
        "pcttuple":  lambda s: '"%s" %% ("HEAD", "632")'
                               % s.replace("HEAD", "%s").replace("632", "%s"),
    }
    py_car = {
        "print":     "print(%s)",
        "syswrite":  "sys.stdout.write(%s)",
        "oswrite":   "os.write(1, %s)",
        "assign":    "_v481 = %s",
        "logging":   "logging.info(%s)",
        "subproc":   'subprocess.run(["printf", %s])',
        # --- T481 additions ---
        "stderr":    "sys.stderr.write(%s)",
        "raise":     "raise RuntimeError(%s)",
        "returned":  "def _f481():\n    return %s",
        "dictval":   '_d481 = {"k": %s}',
        "bare-expr": "%s",              # a bare string EXPRESSION STATEMENT: inert by design
    }

    # ---- tag placements: T476 enumerates 3, this enumerates 6 --------------------------
    #   graded == 1  the tag is NOT printed -> the payload MUST be flagged (abuse B)
    #   graded == 2  the tag IS printed     -> the payload must NOT be flagged
    #   graded == 0  no tag anywhere        -> flagged (predicate 1 or 2 may do it)
    placements = ("trailing-comment", "untagged", "tag-inside",
                  "tag-prev-line", "tag-next-line", "tag-inside-2nd")

    def build(carrier, litfn, place, ext):
        pre = post = ""
        body = litfn(S1)
        if place == "tag-inside":
            body = litfn("[%s] %s" % (TAG, S1))
        elif place == "tag-inside-2nd":
            # the tag is printed, but on the SECOND physical line of the payload. Only
            # reachable where the literal spans lines; elsewhere it degenerates to
            # tag-inside, and that degeneration is recorded rather than skipped.
            body = litfn(S1 + " [%s]" % TAG)
        line = carrier % body
        if place == "trailing-comment":
            line += ("  # " if ext == "sh" else "  # ") + TAG
        elif place == "tag-prev-line":
            pre = "# " + TAG + "\n"
        elif place == "tag-next-line":
            post = "# " + TAG + "\n"
        graded = {"trailing-comment": 1, "untagged": 0, "tag-inside": 2,
                  "tag-prev-line": 1, "tag-next-line": 1, "tag-inside-2nd": 2}[place]
        return pre + line + "\n" + post, graded

    cases = []
    for cn, car in sorted(sh_car.items()):
        for ln, lit in sorted(sh_lit.items()):
            for pl in placements:
                body, graded = build(car, lit, pl, "sh")
                cases.append(("sh/%s/%s/%s" % (cn, ln, pl), "fixture.sh",
                              GOOD_SH + body, graded))
    for cn, car in sorted(py_car.items()):
        for ln, lit in sorted(py_lit.items()):
            for pl in placements:
                body, graded = build(car, lit, pl, "py")
                text = GOOD_PY + body
                cases.append(("py/%s/%s/%s" % (cn, ln, pl), "fixture.py", text, graded))
                # THE FILE-TYPE AXIS T476 DOES NOT HAVE: the same bytes in a .py that will
                # NOT parse, which takes the lexical fallback. A fallback is behaviour under
                # test, not an escape from the matrix.
                cases.append(("pyNP/%s/%s/%s" % (cn, ln, pl), "fixture.py",
                              text + "\nthis is ( not python\n", graded))
    return cases


def main():
    if len(sys.argv) != 5:
        sys.stderr.write("REFUSED: usage: <repo> <ref-T455> <ref-T467> <ref-T476>\n")
        return 3
    repo, r455, r467, r476 = sys.argv[1:5]
    ns = {"T455": lift(repo, r455), "T467": lift(repo, r467), "T476": lift(repo, r476)}
    for k, ref in (("T455", r455), ("T467", r467), ("T476", r476)):
        print("  rule %-5s lifted from %s  names: %s"
              % (k, ref, " ".join(sorted(ns[k]["_names"]))))
    FC, TAG = ns["T476"]["FALSE_CLAIMS"], ns["T476"]["TAG"]
    if ns["T455"]["FALSE_CLAIMS"] != FC or ns["T467"]["FALSE_CLAIMS"] != FC:
        print("REFUSED: the three refs do not grade the same claim table.")
        return 3
    bad = []

    # ---- 0. ARM 1 IS T455's RULE, BEHAVIOURALLY, NOT BY EYE ---------------------------
    print()
    print("=== 0. IS ARM 1 THE RULE IT CLAIMS TO BE? ===")
    probe_lines = []
    for pre in ("", "  ", "\t", "x=1; "):
        for tok in ("echo ", "echo\t", "print(", "printf ", ">&2 echo ", "eecho "):
            for tail in ('"a" # b', "a # b", '"a#b"', "a\\", "'a' # QUOTED", ""):
                probe_lines.append(pre + tok + tail)
    e455, e476 = ns["T455"].get("emitted_payload"), ns["T476"].get("emitter_payloads")
    if e455 is None or e476 is None:
        print("REFUSED: could not lift both emitter rules.")
        return 3
    mism = []
    for ln in probe_lines:
        want = e455(ln)
        got = e476(ln)
        got_v = got[0][1] if got else None
        if want != got_v:
            mism.append((ln, want, got_v))
    print("  probe lines: %d   ARM 1 disagrees with T455's emitted_payload on: %d"
          % (len(probe_lines), len(mism)))
    for m in mism[:5]:
        print("    DISAGREE %r  T455=%r  ARM1=%r" % m)
    if mism:
        bad.append("ARM 1 is not T455's rule: %d disagreements" % len(mism))

    # ---- 1. THE CROSS PRODUCT ---------------------------------------------------------
    cases = matrix(FC, TAG)
    print()
    print("=== 1. THE CROSS PRODUCT: %d cases ===" % len(cases))
    npar = sum(1 for c in cases if c[1].endswith(".py") and _parses(c[2]))
    print("  of the %d python-file cases, %d parse; the rest exercise the lexical fallback"
          % (sum(1 for c in cases if c[1].endswith(".py")), npar))
    caught, p2only, raised = {}, {}, {}
    for name in ("T455", "T467", "T476"):
        c, p2, rs = set(), set(), []
        for cid, rel, text, _g in cases:
            try:
                u, q, p = ns[name]["grade"](text, rel)
            except Exception as exc:
                rs.append((cid, type(exc).__name__))
                continue
            if u or p:
                c.add(cid)
            if p:
                p2.add(cid)
        caught[name], p2only[name], raised[name] = c, p2, rs
        print("  %-5s catches %4d of %d   (predicate 2 alone: %4d)   RAISED on %d"
              % (name, len(c), len(cases), len(p2), len(rs)))
        for cid, exc in rs[:6]:
            print("      RAISED %-52s %s" % (cid, exc))
        if name == "T476" and rs:
            bad.append("T476 raised on %d generated cases" % len(rs))

    print()
    regress = sorted(caught["T455"] - caught["T476"])
    print("  ACCEPTANCE -- cases T455 catches and T476 MISSES: %d" % len(regress))
    for cid in regress:
        print("    REGRESSION %s" % cid)
        bad.append("regression on %s" % cid)
    lost467 = sorted(caught["T455"] - caught["T467"])
    print("  cases T455 catches and T467 misses (the defect under repair): %d" % len(lost467))
    for cid in lost467:
        print("    T467 LOSES %s" % cid)
    print("  cases T476 catches that T467 does not: %d"
          % len(caught["T476"] - caught["T467"]))
    print("  cases T467 catches that T476 does not: %d"
          % len(caught["T467"] - caught["T476"]))
    for cid in sorted(caught["T467"] - caught["T476"]):
        print("    T476 LOSES WHAT T467 CAUGHT: %s" % cid)
        bad.append("T476 loses %s which T467 caught" % cid)

    # ---- 2. DISCRIMINATION: a printed tag must not be flagged --------------------------
    print()
    print("=== 2. DISCRIMINATION -- cases whose tag IS PRINTED, flagged by PREDICATE 2 ===")
    for name in ("T455", "T467", "T476"):
        fp = sorted(cid for cid, rel, text, g in cases if g == 2 and cid in p2only[name])
        print("  %-5s flags %3d correctly tagged payloads" % (name, len(fp)))
        if name == "T476":
            for cid in fp[:40]:
                print("    FLAGS A TAGGED PAYLOAD: %s" % cid)
            t476_fp = fp
    # a tagged payload flagged by T476 but NOT by T467 is a false positive this repair ADDS
    added_fp = sorted(set(t476_fp) - set(cid for cid, rel, text, g in cases
                                         if g == 2 and cid in p2only["T467"]))
    print("  of those, NEW since T467: %d" % len(added_fp))
    for cid in added_fp:
        print("    NEW FALSE POSITIVE ON A TAGGED PAYLOAD: %s" % cid)

    # ---- 3. IS ARM 1 LOAD-BEARING? -----------------------------------------------------
    print()
    print("=== 3. ARM 1 UNWIRED, IN THE LIFTED CODE: which cases does it DECIDE? ===")
    n2 = lift(repo, r476)
    n2["emitter_payloads"] = lambda text: []
    gb2 = n2["grade_binding"]
    noarm1 = set()
    p2_noarm1 = set()
    for cid, rel, text, _g in cases:
        try:
            u, q, p = gb2(text, rel)
        except Exception:
            continue
        if u or p:
            noarm1.add(cid)
        if p:
            p2_noarm1.add(cid)
    decided = sorted(p2only["T476"] - p2_noarm1)
    print("  predicate-2 cases the union sees WITH ARM 1 and loses WITHOUT it: %d"
          % len(decided))
    ab_catch = [cid for cid in decided
                if [g for c2, r2, t2, g in cases if c2 == cid][0] in (0, 1)]
    ab_fp = [cid for cid in decided
             if [g for c2, r2, t2, g in cases if c2 == cid][0] == 2]
    print("    of which ABUSES (ARM 1 earns a real catch): %d" % len(ab_catch))
    for cid in ab_catch[:40]:
        print("      ARM 1 EARNS: %s" % cid)
    print("    of which CORRECTLY TAGGED payloads (ARM 1 causes a FALSE POSITIVE): %d"
          % len(ab_fp))
    for cid in ab_fp[:40]:
        print("      ARM 1 COSTS: %s" % cid)
    print("  cases lost from the WHOLE verdict (predicate 1 or 2) without ARM 1: %d"
          % len(caught["T476"] - noarm1))

    # ---- 4. ARM 1 vs ARM 3 AS SETS ON SHELL TEXT ---------------------------------------
    print()
    print("=== 4. CAN THE SUPERSET CONTROL FAIL? ARM 1's payloads vs the OTHER arms' ===")
    n3 = lift(repo, r476)
    n3["emitter_payloads"] = lambda text: []
    others = n3["printed_payloads"]
    arm1 = ns["T476"]["emitter_payloads"]
    sh_covered = py_covered = sh_total = py_total = 0
    sh_un, py_un = [], []
    for cid, rel, text, _g in cases:
        a = set(arm1(text))
        if not a:
            continue
        try:
            o = set(others(text, rel))
        except Exception:
            continue
        if rel.endswith(".sh"):
            sh_total += 1
            if a <= o:
                sh_covered += 1
            else:
                sh_un.append(cid)
        else:
            py_total += 1
            if a <= o:
                py_covered += 1
            else:
                py_un.append(cid)
    print("  shell cases where ARM 1's payload set is ALREADY a subset of the other arms': "
          "%d of %d" % (sh_covered, sh_total))
    print("  python cases where it is:                                                    "
          "%d of %d" % (py_covered, py_total))
    print("  => the SUPERSET CONTROL can only fail on fixtures where ARM 1 contributes a")
    print("     payload no other arm produces. On shell text with no continuation the other")
    print("     arms reproduce ARM 1's payload EXACTLY, so those fixtures cannot redden it.")
    print("  shell cases that WOULD redden it: %d  %s" % (len(sh_un), sh_un[:6]))
    print("  python cases that WOULD redden it: %d  %s" % (len(py_un), py_un[:6]))
    if not (sh_un or py_un):
        bad.append("no generated case can redden the SUPERSET CONTROL")

    print()
    if bad:
        print("RESULT: %d relation(s) did NOT hold." % len(bad))
        for b in bad:
            print("  - %s" % b)
        return 1
    print("RESULT: every recorded relation held. EXIT 0")
    return 0


def _parses(text):
    try:
        ast.parse(text)
        return True
    except (SyntaxError, ValueError):
        return False


if __name__ == "__main__":
    sys.exit(main())
