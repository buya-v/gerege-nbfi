#!/usr/bin/env python3
"""T481 -- THE WIDENING T476 REJECTED, RE-MEASURED. ITS NUMBERS ARE IN THE SHIPPED DOCSTRING.

`printed_payloads` publishes, beside the rule, the measurement that decided against running
the lexical arm over a .py that PARSES:

    "Running it there raises the false-positive count over the 1,687 tracked .py/.sh from
     6 to 9, flags THIS FILE (a guarded file -- the guard would be red on a clean tree), and
     fires on the inert-DOCSTRING control."

A measurement published beside a rule is a claim the next reader will cite, so it is
re-derived here rather than accepted: the widened rule is built by MUTATING THE LIFTED CODE
(dropping the `.py`-parses early return so ARM 3 runs everywhere), never by retyping it, and
the population is every tracked .py/.sh at the ref.

It also re-measures the second half of the same sentence -- whether the widened rule fires on
the shipped inert-docstring fixture -- and, because that is the sentence ARM 1 itself has to
answer to, whether ARM 1 fires on a docstring of its own.

  python3 90-t481-rejected-widening.py <repo> <code-ref> [<population-ref>]

The two refs are separate because the docstring publishes its figure over the population at
the EARLIER ref (1,687 files) while the code that can be widened exists only at the tip.

EXIT 0  measured.  EXIT 3  REFUSED.
"""
import ast
import subprocess
import sys

S = ".softhouse"
GRADER = S + "/reviews/A2-11/verify-capture-integrity.py"
WANT = ("FALSE_CLAIMS", "TAG", "_CONVERSION", "_FIELD", "states_a_false_claim",
        "strip_trailing_comment", "strip_trailing_comment_posix", "quoted_segments",
        "join_continuations", "squeeze", "_fold", "python_payloads", "emitter_payloads",
        "printed_payloads", "tagged_blocks", "grade_binding")
WIDEN_OLD = ("    if rel.endswith(\".py\"):\n"
             "        try:\n"
             "            return out + python_payloads(text)\n"
             "        except (SyntaxError, ValueError):\n"
             "            pass\n")
WIDEN_NEW = ("    if rel.endswith(\".py\"):\n"
             "        try:\n"
             "            out = out + python_payloads(text)\n"
             "        except (SyntaxError, ValueError):\n"
             "            pass\n")


def git(repo, *a):
    p = subprocess.run(["git", "-C", repo] + list(a), capture_output=True)
    if p.returncode != 0:
        sys.stderr.write("REFUSED: git failed\n")
        sys.exit(3)
    return p.stdout


def ns_from(src, tag):
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
    exec(compile("import ast, os, re, sys\n\n" + "\n\n".join(pieces), tag, "exec"), ns)
    return ns


def corpus(repo, ref):
    names = [f for f in git(repo, "ls-tree", "-r", "--name-only", ref).decode().split("\n")
             if f.endswith(".py") or f.endswith(".sh")]
    spec = "".join("%s:%s\n" % (ref, f) for f in names).encode()
    p = subprocess.run(["git", "-C", repo, "cat-file", "--batch"], input=spec,
                       capture_output=True)
    buf, out, i = p.stdout, {}, 0
    for f in names:
        nl = buf.index(b"\n", i)
        size = int(buf[i:nl].decode().split()[2])
        out[f] = buf[nl + 1:nl + 1 + size].decode("utf-8", "replace")
        i = nl + 1 + size + 1
    return out


def main():
    if len(sys.argv) not in (3, 4):
        sys.stderr.write("REFUSED: usage: <repo> <code-ref> [<population-ref>]\n")
        return 3
    repo, ref = sys.argv[1:3]
    popref = sys.argv[3] if len(sys.argv) == 4 else ref
    src = git(repo, "show", "%s:%s" % (ref, GRADER)).decode("utf-8", "replace")
    if WIDEN_OLD not in src:
        sys.stderr.write("REFUSED: the early-return anchor is absent; the widening would be "
                         "a no-op and a no-op must never read as a measurement.\n")
        return 3
    base = ns_from(src, "<base>")
    wide = ns_from(src.replace(WIDEN_OLD, WIDEN_NEW, 1), "<wide>")
    probe = 'print("x")  # y\n'
    if base["printed_payloads"](probe, "f.py") == wide["printed_payloads"](probe, "f.py"):
        sys.stderr.write("REFUSED: the widening changed nothing on a probe .py.\n")
        return 3
    texts = corpus(repo, popref)
    print("  code from %s   population from %s: %d tracked .py/.sh"
          % (ref, popref, len(texts)))
    out = {}
    for name, ns in (("shipped", base), ("widened", wide)):
        hits = set()
        for f, t in texts.items():
            try:
                u, q, p = ns["grade_binding"](t, f)
            except Exception:
                continue
            if p:
                hits.add(f)
        out[name] = hits
        print("  %-8s flags %d file(s)" % (name, len(hits)))
    print("  files the WIDENING adds:")
    for f in sorted(out["widened"] - out["shipped"]):
        print("      %s" % f)
    print("  does the widening flag the grader itself (a GUARDED file)? %s"
          % any(f.endswith("/verify-capture-integrity.py") for f in out["widened"]))
    print()
    TAG, FC = base["TAG"], base["FALSE_CLAIMS"]
    S1 = "There is no " + FC[3] + "."
    inert_doc = '"""a docstring\n[%s] "%s"\n"""\n' % (TAG, S1)
    doc_with_print = ('print("  [%s] %s")\n' % (TAG, S1)
                      + 'def _f():\n    """d\nprint("%s")\n    """\n' % S1)
    print("  === THE INERT-DOCSTRING SENTENCE, HELD TO ITS OWN STANDARD ===")
    print("  shipped rule on the SHIPPED inert-docstring fixture:            %s"
          % ("FLAGS" if base["grade_binding"](inert_doc, "f.py")[2] else "clear"))
    print("  WIDENED rule on the same fixture:                              %s"
          % ("FLAGS" if wide["grade_binding"](inert_doc, "f.py")[2] else "clear"))
    print("  shipped rule on a docstring whose LINE STARTS WITH `print(`:   %s"
          % ("FLAGS" if base["grade_binding"](doc_with_print, "f.py")[2] else "clear"))
    print("      ^ that last line is ARM 1 -- a LEXICAL arm running over a .py that PARSES,")
    print("        which is the thing the rejected widening was rejected for being.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
