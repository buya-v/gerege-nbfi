#!/usr/bin/env python3
"""T167 re-audit: the four files T156's GUARD regex scored `guarded` while they
carry no trap / finally / atexit.  T158 named them; this re-derives the verdict
from the AST rather than from either report (P-48 rule 1, and the whole point of
this finding is that a classifier lied - so a re-audit that trusts a classifier
would be the same defect again).

For each Python file it reports, from the AST and never from source text:
  * try / except / finally / with / atexit.register / signal.signal counts;
  * every mutating call site, with the line number and the argument expression
    as written, so the target of each write can be adjudicated by hand;
  * how many times each guard word appears inside a STRING LITERAL, which is
    what the regex was actually matching.

Shell files get an honest downgrade: there is no shell parser in the standard
library, so they are tokenised with shlex (POSIX mode), which does strip quoted
strings and `#` comments.  That is strictly better than a raw grep and strictly
worse than a parser, and it is labelled as such rather than presented as one.
"""
import ast
import io
import os
import shlex
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

FILES = [
    ".softhouse/capture/pathb/t149/prove-exit-trap.py",
    ".softhouse/capture/pathb/t149/t156-sweep-unguarded-mutators.py",
    ".softhouse/capture/pathb/t99/prove-p24-postmerge.sh",
    ".softhouse/reviews/t47-probe/t47_edit_1.py",     # the one T167 fixed
]

GUARD_WORDS = ("trap", "finally", "atexit", "__exit__", "contextmanager")

MUTATORS = {
    "os.replace", "os.rename", "os.remove", "os.unlink", "os.rmdir",
    "os.truncate", "os.chmod", "os.makedirs", "os.mkdir",
    "shutil.move", "shutil.copy", "shutil.copy2", "shutil.copyfile",
    "shutil.copytree", "shutil.rmtree", "open", "io.open",
}
SH_MUTATORS = ("mv", "cp", "rm", "sed", "git", "tee", "truncate", "install",
               "ln", "chmod", ">", ">>")


def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted(node.value)
        return base + "." + node.attr if base else node.attr
    return ""


def show(node):
    try:
        return ast.unparse(node)
    except Exception:                                     # pragma: no cover
        return "<unparse unavailable>"


def audit_py(rel, src):
    tree = ast.parse(src)
    tries = [n for n in ast.walk(tree) if isinstance(n, ast.Try)]
    finallies = [n for n in tries if n.finalbody]
    handlers = sum(len(n.handlers) for n in tries)
    withs = [n for n in ast.walk(tree) if isinstance(n, (ast.With,
                                                         ast.AsyncWith))]
    atexits, signals = [], []
    mutations = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            name = dotted(n.func)
            if name == "atexit.register":
                atexits.append(n.lineno)
            if name in ("signal.signal", "signal.sigaction"):
                signals.append(n.lineno)
            if name in MUTATORS:
                if name in ("open", "io.open"):
                    mode = ""
                    if len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                        mode = str(n.args[1].value)
                    for kw in n.keywords:
                        if kw.arg == "mode" and isinstance(kw.value,
                                                           ast.Constant):
                            mode = str(kw.value.value)
                    if not any(c in mode for c in "wax+"):
                        continue
                mutations.append((n.lineno, show(n)[:110]))
    in_str = {w: 0 for w in GUARD_WORDS}
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            low = n.value.lower()
            for w in GUARD_WORDS:
                in_str[w] += low.count(w)
    print("  parser              : ast (authoritative for Python)")
    print("  try blocks          : %d   (with a finally: %d, except clauses: %d)"
          % (len(tries), len(finallies), handlers))
    print("  with statements     : %d" % len(withs))
    print("  atexit.register     : %d %s" % (len(atexits), atexits or ""))
    print("  signal.signal       : %d %s" % (len(signals), signals or ""))
    print("  guard words inside STRING LITERALS: %s"
          % {k: v for k, v in in_str.items() if v})
    print("  mutating call sites (%d):" % len(mutations))
    for ln, txt in sorted(mutations):
        print("    :%-4d %s" % (ln, txt))


def audit_sh(rel, src):
    lex = shlex.shlex(src, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    toks = []
    try:
        for t in lex:
            toks.append(t)
    except ValueError as e:
        print("  shlex could not tokenise the whole file (%s); results below "
              "cover the prefix it managed" % e)
    print("  parser              : shlex POSIX tokeniser - NOT a shell parser."
          "\n                        It strips `#` comments and quoted strings,"
          " which is what\n                        the regex failed to do, but "
          "it does not understand\n                        redirections or "
          "compound commands.  Stated, not hidden.")
    hits = {w: 0 for w in GUARD_WORDS}
    for t in toks:
        for w in GUARD_WORDS:
            if t == w or t.startswith(w):
                hits[w] += 1
    print("  guard words as unquoted TOKENS: %s"
          % {k: v for k, v in hits.items() if v})
    raw = sum(src.lower().count(w) for w in GUARD_WORDS)
    print("  guard words anywhere in the raw text (what the regex saw): %d"
          % raw)
    print("  candidate mutating command lines (hand-adjudicate each):")
    found = False
    for i, line in enumerate(src.splitlines(), 1):
        st = line.strip()
        if st.startswith("#") or not st:
            continue
        first = st.split()[0] if st.split() else ""
        if first in SH_MUTATORS or " > " in st or ">>" in st:
            print("    :%-4d %s" % (i, st[:110]))
            found = True
    if not found:
        print("    (none)")


for rel in FILES:
    path = os.path.join(REPO, rel)
    print("\n" + "=" * 78)
    print("== " + rel)
    print("=" * 78)
    if not os.path.exists(path):
        print("  MISSING")
        continue
    src = io.open(path, encoding="utf-8").read()
    print("  bytes               : %d" % os.path.getsize(path))
    if rel.endswith(".py"):
        audit_py(rel, src)
    else:
        audit_sh(rel, src)
