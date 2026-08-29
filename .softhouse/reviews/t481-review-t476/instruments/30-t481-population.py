#!/usr/bin/env python3
"""T481 -- THE FALSE-POSITIVE POPULATION AND THE TWO MEASUREMENTS THE REPAIR CHOICE RESTS ON.

T476 justified "union AND widen, union first" on two numbers, and if either is wrong the
choice is wrong:

  (i)  T455's rule flags ZERO of the tracked .py/.sh, so the union inherits no false
       positives;
  (ii) T476 adds ZERO false positives over T467, and the six flagged files are the same six
       T472 named.

Both are re-derived here from the blobs at each ref, over the WHOLE tracked .py/.sh
population at each ref -- not over the four guarded files. The member SET is printed with the
tree it was measured on, because a count with no members is not checkable.

It also re-derives, at first hand, the three reach cardinals T472 published and T476 says
reproduce exactly (`%`-format sites, f-strings, bytes literals), and T476's own narrower
count of f-strings that have an interpolation BETWEEN two constants -- the number its
disagreement with T472 turns on.

NO REPO-RELATIVE PATH IS SPELLED AS A LITERAL (P-103).

  python3 30-t481-population.py <repo> <ref-T455> <ref-T467> <ref-T476>

EXIT 0  measured.   EXIT 1  a recorded relation did not hold.   EXIT 3  REFUSED.
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
GUARDED_TAILS = ("/verify-capture-integrity.py", "/run-all.sh",
                 "/10-drive-conditions.sh", "/12-relaunder-manifest.py")


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo] + list(args), capture_output=True)
    if p.returncode != 0:
        sys.stderr.write("REFUSED: git %s failed\n" % " ".join(args))
        sys.exit(3)
    return p.stdout


def lift(repo, ref):
    src = git(repo, "show", "%s:%s" % (ref, GRADER)).decode("utf-8", "replace")
    tree, pieces = ast.parse(src), []
    for node in tree.body:
        name = None
        if isinstance(node, ast.FunctionDef):
            name = node.name
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
        if name in WANT:
            pieces.append(ast.get_source_segment(src, node))
    ns = {}
    exec(compile("import ast, os, re, sys\n\n" + "\n\n".join(pieces), "<%s>" % ref, "exec"), ns)
    gb = ns["grade_binding"]
    n = len(inspect.signature(gb).parameters)
    ns["g"] = (lambda t, r: gb(t)) if n == 1 else (lambda t, r: gb(t, r))
    return ns


def corpus(repo, ref):
    names = [f for f in git(repo, "ls-tree", "-r", "--name-only", ref).decode().split("\n")
             if f.endswith(".py") or f.endswith(".sh")]
    spec = "".join("%s:%s\n" % (ref, f) for f in names).encode()
    p = subprocess.run(["git", "-C", repo, "cat-file", "--batch"], input=spec,
                       capture_output=True)
    if p.returncode != 0:
        sys.stderr.write("REFUSED: cat-file --batch failed\n")
        sys.exit(3)
    buf, out, i = p.stdout, {}, 0
    for f in names:
        nl = buf.index(b"\n", i)
        size = int(buf[i:nl].decode().split()[2])
        out[f] = buf[nl + 1:nl + 1 + size].decode("utf-8", "replace")
        i = nl + 1 + size + 1
    return out


def flags(ns, texts):
    hits, raised = {}, {}
    for f, t in texts.items():
        try:
            u, q, p = ns["g"](t, f)
        except Exception as exc:
            raised[f] = type(exc).__name__
            continue
        if p:
            hits[f] = p
    return hits, raised


def main():
    if len(sys.argv) != 5:
        sys.stderr.write("REFUSED: usage: <repo> <T455> <T467> <T476>\n")
        return 3
    repo, r455, r467, r476 = sys.argv[1:5]
    ns = {"T455": lift(repo, r455), "T467": lift(repo, r467), "T476": lift(repo, r476)}
    bad = []
    for ref_label, ref in (("6a345e4a-equivalent (T467 tip)", r467), ("T476 tip", r476)):
        texts = corpus(repo, ref)
        print()
        print("=== POPULATION AT %s: %d tracked .py/.sh ===" % (ref_label, len(texts)))
        hits = {}
        for name in ("T455", "T467", "T476"):
            h, raised = flags(ns[name], texts)
            hits[name] = h
            print("  %-5s flags %d file(s); grading RAISED on %d" % (name, len(h), len(raised)))
            for f, why in sorted(raised.items())[:8]:
                print("      RAISED %-68s %s" % (f, why))
            if name == "T476" and raised:
                bad.append("T476 raises on %d corpus members at %s" % (len(raised), ref_label))
        if ref == r476:
            print()
            print("  (i)  T455's rule flags %d of %d -- the number the union's cost rests on"
                  % (len(hits["T455"]), len(texts)))
            print("  (ii) the T476 member SET, at this tree:")
            for f in sorted(hits["T476"]):
                print("       %s" % f)
                for site in hits["T476"][f][:2]:
                    print("           %s" % site)
            print("  T476 vs T467:  +%d  -%d"
                  % (len(set(hits["T476"]) - set(hits["T467"])),
                     len(set(hits["T467"]) - set(hits["T476"]))))
            for f in sorted(set(hits["T476"]) - set(hits["T467"])):
                print("       NEW UNDER T476: %s" % f)
                bad.append("T476 adds a false positive: %s" % f)
            for f in sorted(set(hits["T467"]) - set(hits["T476"])):
                print("       LOST UNDER T476: %s" % f)
                bad.append("T476 stops flagging %s" % f)
            guarded = [f for f in texts if f.endswith(GUARDED_TAILS)]
            red = [f for f in guarded if f in hits["T476"]]
            print("  the %d guarded files, flagged by T476 on a clean tree: %d %s"
                  % (len(guarded), len(red), red))
            if red:
                bad.append("a guarded file is flagged on a clean tree")

    # ---- the reach cardinals both reviews publish -------------------------------------
    print()
    print("=== REACH CARDINALS, re-counted at %s (T472 published 7152/571, 2491/170, 192/60)"
          % r467)
    texts = corpus(repo, r467)
    pct = pctf = fs = fsf = by = byf = 0
    interp = interpf = 0
    for f, t in sorted(texts.items()):
        if not f.endswith(".py"):
            continue
        try:
            tree = ast.parse(t)
        except (SyntaxError, ValueError):
            continue
        a = b = c = d = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod) \
                    and isinstance(node.left, ast.Constant) \
                    and isinstance(node.left.value, str):
                a += 1
            if isinstance(node, ast.JoinedStr):
                b += 1
                vals = node.values
                for i in range(1, len(vals) - 1):
                    if isinstance(vals[i], ast.FormattedValue) \
                            and isinstance(vals[i - 1], ast.Constant) \
                            and isinstance(vals[i + 1], ast.Constant):
                        d += 1
                        break
            if isinstance(node, ast.Constant) and isinstance(node.value, bytes):
                c += 1
        pct += a
        fs += b
        by += c
        interp += d
        pctf += 1 if a else 0
        fsf += 1 if b else 0
        byf += 1 if c else 0
        interpf += 1 if d else 0
    print('  "<literal>" %% ...      sites=%d  files=%d' % (pct, pctf))
    print("  f-strings              sites=%d  files=%d" % (fs, fsf))
    print("  bytes literals         sites=%d  files=%d" % (by, byf))
    print("  f-strings with an interpolation BETWEEN two constants: %d in %d files"
          % (interp, interpf))
    print("  (that last row is T476's narrower count -- the shape where a claim COULD be")
    print("   split by an interpolation. T476 publishes 1,033 in 158 files.)")

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
