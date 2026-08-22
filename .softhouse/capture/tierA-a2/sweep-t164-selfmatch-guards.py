#!/usr/bin/env python3
"""T164 -- P-26 CONCEPT SWEEP: which other guards under .softhouse/ can be kept green by
prose?

  python3 sweep-t164-selfmatch-guards.py [<repo-root>]

THE CONCEPT, NOT THE SENTENCE
-----------------------------
The sentence T164 was handed is "`analyze7.py`'s float guard greps for `parse_float` and
matches its own docstring". The CONCEPT is:

    AN ASSERTION WHOSE EVIDENCE IS A LITERAL TOKEN SEARCHED FOR IN WHOLE-FILE SOURCE
    TEXT, WHERE THAT TOKEN ALSO OCCURS IN PROSE -- A COMMENT, A DOCSTRING, OR A STRING
    LITERAL -- SO THE ASSERTION CAN BE SATISFIED WITHOUT THE CODE BEING TRUE.

so this sweep looks for that shape wherever it is, and reports BOTH TERMS (P-67): how many
source-grep assertion sites exist, and how many of those have the self-match hole.

TWO VARIANTS OF THE HOLE, BOTH MEASURED AND REPORTED SEPARATELY
---------------------------------------------------------------
  TARGET-PROSE   the token occurs in the prose of the file BEING GRADED. This is
                 analyze7.py's case: the guard lives in prove-mkreq7-guard-red.py, the
                 prose is analyze7.py's docstring.
  SELF-PROSE     the grepping file greps ITSELF (or a file it also is), and the token
                 occurs in its own prose.

HOW A SITE IS FOUND (AST for Python -- P-75: no bare grep in a committed instrument)
------------------------------------------------------------------------------------
Pass 1 binds variables that hold WHOLE-FILE SOURCE TEXT:
    X = open(<path>).read()                     X = open(<path>, ...).read()
    X = Path(<path>).read_text()                X = <f>.read()   inside `with open(..) as f`
and records the path expression, resolving `os.path.join(DIR, "name.py")` and plain
constants to a filename.

Pass 2 finds LITERAL-TOKEN TESTS against those variables:
    "<const>" in X            "<const>" not in X          X.count("<const>")
    X.find("<const>")         re.<fn>("<const-pattern>", X)
    "<const>" in X.replace(..)  and other method chains rooted at X

Shell scripts are handled textually (`grep`/`git grep`/`rg` with a literal pattern and a
file operand) and Go with a regex for `strings.Contains(src, "lit")`. Both are STATED
LIMITATIONS, not silent ones -- see WHAT WAS SKIPPED at the end of the run.

THE PROSE TEST is not a substring search over the whole file. The target is TOKENIZED
(`tokenize` for Python), so COMMENT and STRING tokens are separated from code, and the
question asked is the honest one:

    does this token occur in the target's PROSE, and would the assertion still be
    satisfied if every CODE occurrence were deleted?

A site is flagged HOLE only when the answer to both halves is yes.

NIL COVERAGE IS AN ERROR. 0 files walked, or 0 assertion sites found, exits non-zero:
a sweep that finds nothing and reports success is the defect being swept for (P-45).

WHAT THIS SWEEP DOES NOT DO -- stated so it is not read as exhaustive (P-40/P-66)
-----------------------------------------------------------------------------------
It reports. It fixes nothing outside `.softhouse/capture/tierA-a2/`, which is T164's
files_hint; everything else is a BACKLOG ITEM. Counts of what was skipped, and why, are
printed at the end of every run.
"""
import ast
import io
import os
import re
import sys
import tokenize

DEFAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            "..", "..", ".."))
SOFTHOUSE = ".softhouse"
RE_METHODS = ("search", "match", "findall", "finditer", "fullmatch", "sub", "subn",
              "split", "compile")
TEXT_TESTS = ("count", "find", "rfind", "index", "startswith", "endswith", "__contains__")


# ------------------------------------------------------------------ prose classification
def python_prose_and_code(src):
    """(prose_text, code_text) for a Python source: comments+strings vs everything else."""
    prose, code = [], []
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return None, None
    for t in toks:
        if t.type == tokenize.COMMENT or t.type == tokenize.STRING:
            prose.append(t.string)
        elif t.type not in (tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
                            tokenize.DEDENT, tokenize.ENDMARKER):
            code.append(t.string)
    return "\n".join(prose), "\n".join(code)


def generic_prose_and_code(src, comment_prefixes=("#",)):
    """Line-oriented fallback for shell/Go: a line's comment tail is prose."""
    prose, code = [], []
    for line in src.split("\n"):
        cut = None
        for p in comment_prefixes:
            i = line.find(p)
            if i >= 0 and (cut is None or i < cut):
                cut = i
        if cut is None:
            code.append(line)
        else:
            code.append(line[:cut])
            prose.append(line[cut:])
    return "\n".join(prose), "\n".join(code)


# ------------------------------------------------------------------------ python scanner
class PySite(object):
    def __init__(self, gfile, lineno, token, target_expr, target_file, shape, ctx=None):
        self.gfile, self.lineno, self.token = gfile, lineno, token
        self.target_expr, self.target_file, self.shape = target_expr, target_file, shape
        self.ctx = ctx


def unparse(n):
    try:
        return ast.unparse(n)
    except Exception:
        return "<unparseable>"


def resolve_path_expr(node):
    """Best-effort filename out of a path expression; None when it is not static."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return os.path.basename(node.value), node.value
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
            and node.func.attr == "join":
        parts = [a for a in node.args
                 if isinstance(a, ast.Constant) and isinstance(a.value, str)]
        if parts:
            return os.path.basename(parts[-1].value), parts[-1].value
    if isinstance(node, ast.Call) and node.args:
        return resolve_path_expr(node.args[0])
    return None, None


def source_vars(tree):
    """{varname: (path_basename, path_text, expr_text)} for whole-file reads."""
    out = {}

    def note(target, call, path_node):
        if not isinstance(target, ast.Name):
            return
        base, full = resolve_path_expr(path_node) if path_node is not None else (None, None)
        out[target.id] = (base, full, unparse(call))

    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and len(n.targets) == 1:
            v = n.value
            if isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute):
                if v.func.attr in ("read", "read_text"):
                    inner = v.func.value
                    path_node = inner.args[0] if isinstance(inner, ast.Call) and inner.args \
                        else None
                    note(n.targets[0], v, path_node)
        if isinstance(n, ast.With):
            for item in n.items:
                if isinstance(item.context_expr, ast.Call) \
                        and isinstance(item.context_expr.func, ast.Name) \
                        and item.context_expr.func.id == "open" \
                        and isinstance(item.optional_vars, ast.Name):
                    fh = item.optional_vars.id
                    path_node = item.context_expr.args[0] if item.context_expr.args else None
                    for m in ast.walk(n):
                        if isinstance(m, ast.Assign) and len(m.targets) == 1 \
                                and isinstance(m.value, ast.Call) \
                                and isinstance(m.value.func, ast.Attribute) \
                                and m.value.func.attr == "read" \
                                and isinstance(m.value.func.value, ast.Name) \
                                and m.value.func.value.id == fh:
                            note(m.targets[0], m.value, path_node)
    return out


ASSERTISH = re.compile(
    r'(?i)^(check|assert|expect|require|verif|guard|must|ensure|fail|refuse|prove|deny)')
FAILURE_SINK = re.compile(r'(?i)(sys\.exit|SystemExit|raise |FAIL|failures|refus|abort)')


def parent_map(tree):
    par = {}
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n):
            par[c] = n
    return par


def assertion_context(node, par):
    """Is this literal-token test WIRED TO A VERDICT? Returns the reason, or None.

    A generator that splices a Java snippet and a guard that grades a file both contain
    `"tok" in src`. Only the second is a guard, and counting them together would inflate
    TERM 1 and make TERM 2's ratio meaningless (P-67: both terms have to mean something).
    """
    cur, hops = node, 0
    while cur in par and hops < 12:
        cur = par[cur]
        hops += 1
        if isinstance(cur, ast.Assert):
            return "assert statement"
        if isinstance(cur, ast.Call):
            f = cur.func
            name = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
            if name and ASSERTISH.match(name):
                return "argument to %s(...)" % name
        if isinstance(cur, ast.If):
            try:
                body = "\n".join(unparse(x) for x in cur.body + cur.orelse)
            except Exception:
                body = ""
            if FAILURE_SINK.search(body):
                return "if-test whose branch reaches a failure sink"
    return None


def root_name(node):
    """The Name at the root of a method chain, e.g. src.replace(..).lower() -> 'src'."""
    while isinstance(node, (ast.Attribute, ast.Call, ast.Subscript)):
        node = node.func.value if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
            else (node.value if isinstance(node, (ast.Attribute, ast.Subscript)) else None)
        if node is None:
            return None
    return node.id if isinstance(node, ast.Name) else None


def scan_python(path, rel):
    src = open(path, encoding="utf-8", errors="replace").read()
    try:
        tree = ast.parse(src, filename=rel)
    except SyntaxError:
        return None, "SyntaxError"
    svars = source_vars(tree)
    if not svars:
        return [], None
    par = parent_map(tree)
    sites = []

    def add(node, token, var, shape):
        base, full, expr = svars[var]
        sites.append(PySite(rel, node.lineno, token, expr, full or base, shape,
                            assertion_context(node, par)))

    for n in ast.walk(tree):
        if isinstance(n, ast.Compare) and len(n.ops) == 1 \
                and isinstance(n.ops[0], (ast.In, ast.NotIn)) \
                and isinstance(n.left, ast.Constant) and isinstance(n.left.value, str):
            rn = root_name(n.comparators[0])
            if rn in svars:
                add(n, n.left.value, rn,
                    "'%s' %s %s" % (n.left.value,
                                    "in" if isinstance(n.ops[0], ast.In) else "not in",
                                    unparse(n.comparators[0])))
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            if n.func.attr in TEXT_TESTS and n.args \
                    and isinstance(n.args[0], ast.Constant) \
                    and isinstance(n.args[0].value, str):
                rn = root_name(n.func.value) if not isinstance(n.func.value, ast.Name) \
                    else n.func.value.id
                if rn in svars:
                    add(n, n.args[0].value, rn, unparse(n))
            elif n.func.attr in RE_METHODS and isinstance(n.func.value, ast.Name) \
                    and n.func.value.id == "re" and len(n.args) >= 2 \
                    and isinstance(n.args[0], ast.Constant) \
                    and isinstance(n.args[0].value, str):
                rn = root_name(n.args[1]) if not isinstance(n.args[1], ast.Name) \
                    else n.args[1].id
                if rn in svars:
                    add(n, n.args[0].value, rn, unparse(n))
    return sites, None


# ---------------------------------------------------------------------- shell / go scan
RE_SH_GREP = re.compile(
    r'(?:^|[|;&(]|\$\()\s*(?:LC_ALL=\S+\s+)?(?:/usr/bin/)?(?:git\s+)?(grep|rg|ugrep)\b'
    r'(?P<flags>(?:\s+-[^\s]+)*)\s+'
    r'(?P<quote>[\'"])(?P<pat>[^\'"]{2,})(?P=quote)\s+(?P<file>[^\s|;&)]+)')
SH_EVIDENCE = re.compile(r'\|\|\s*(true|echo)|\|\s*head\b|\|\s*sed\b|^\s*echo\b')


def sh_context(src, lineno, prefixes=("#",)):
    """Heuristic verdict-wiring test for a shell/Go line. Stated as a heuristic."""
    lines = src.split("\n")
    line = lines[lineno - 1]
    if SH_EVIDENCE.search(line):
        return None                     # an evidence dump, not an assertion
    window = "\n".join(lines[max(0, lineno - 3):lineno + 2])
    if re.search(r'(?i)\b(if|exit|fail|assert|\&\&|\|\|)\b', window) \
            and not SH_EVIDENCE.search(line):
        return "shell line near a conditional or exit (HEURISTIC, not an AST)"
    return None


RE_GO_CONTAINS = re.compile(r'strings\.Contains\(\s*([A-Za-z_][\w.]*)\s*,\s*"([^"]{2,})"\s*\)')


def walk(root):
    files = []
    for dirpath, dirnames, filenames in os.walk(os.path.join(root, SOFTHOUSE)):
        dirnames[:] = sorted(d for d in dirnames if d != ".git")
        for f in sorted(filenames):
            files.append(os.path.join(dirpath, f))
    return files


def main(argv):
    root = os.path.abspath(argv[1]) if len(argv) > 1 else DEFAULT_ROOT
    print("=" * 78)
    print("T164 -- P-26 concept sweep: source-grep assertions kept green by prose")
    print("=" * 78)
    print("ROOT: %s/%s" % (root, SOFTHOUSE))
    print()

    allfiles = walk(root)
    if not allfiles:
        print("REFUSING: 0 files under %s/%s -- INSPECTED NOTHING." % (root, SOFTHOUSE),
              file=sys.stderr)
        return 2

    py = [f for f in allfiles if f.endswith(".py")]
    sh = [f for f in allfiles if f.endswith((".sh", ".zsh", ".bash"))]
    go = [f for f in allfiles if f.endswith(".go")]
    other = [f for f in allfiles if f not in set(py) | set(sh) | set(go)]

    print("POPULATION WALKED")
    print("  files under .softhouse/ ......... %d" % len(allfiles))
    print("  .py  (AST-scanned) ............. %d" % len(py))
    print("  .sh/.zsh/.bash (regex-scanned) . %d" % len(sh))
    print("  .go  (regex-scanned) ........... %d" % len(go))
    print("  SKIPPED, not instruments ....... %d  (.md .json .txt .http .status .sql ...)"
          % len(other))
    print()

    # ---- cache of prose/code per target file
    cache = {}

    def prose_code(abspath):
        if abspath in cache:
            return cache[abspath]
        try:
            src = open(abspath, encoding="utf-8", errors="replace").read()
        except OSError:
            cache[abspath] = (None, None)
            return cache[abspath]
        if abspath.endswith(".py"):
            r = python_prose_and_code(src)
            if r[0] is None:
                r = generic_prose_and_code(src)
        elif abspath.endswith(".go"):
            r = generic_prose_and_code(src, ("//",))
        else:
            r = generic_prose_and_code(src, ("#",))
        cache[abspath] = r
        return r

    sites = []            # (kind, gfile_rel, lineno, token, target_rel_or_None, shape)
    unparsed = []
    for f in py:
        rel = os.path.relpath(f, root)
        s, err = scan_python(f, rel)
        if err:
            unparsed.append((rel, err))
            continue
        for x in s:
            sites.append(("py", rel, x.lineno, x.token, x.target_file, x.shape, x.ctx))
    for f in sh:
        rel = os.path.relpath(f, root)
        src = open(f, encoding="utf-8", errors="replace").read()
        for i, line in enumerate(src.split("\n"), 1):
            if line.lstrip().startswith("#"):
                continue
            m = RE_SH_GREP.search(line)
            if m:
                sites.append(("sh", rel, i, m.group("pat"), m.group("file"),
                              line.strip()[:110], sh_context(src, i)))
    for f in go:
        rel = os.path.relpath(f, root)
        src = open(f, encoding="utf-8", errors="replace").read()
        for i, line in enumerate(src.split("\n"), 1):
            if line.lstrip().startswith("//"):
                continue
            m = RE_GO_CONTAINS.search(line)
            if m:
                sites.append(("go", rel, i, m.group(2), None, line.strip()[:110],
                              sh_context(src, i, ("//",))))

    if not sites:
        print("REFUSING: 0 source-grep assertion sites found across %d instrument file(s). "
              "INSPECTED NOTHING useful -- a sweep that finds nothing and reports success "
              "is the defect being swept for (P-45)." % (len(py) + len(sh) + len(go)),
              file=sys.stderr)
        return 2

    # ---- resolve targets and classify
    holes, clean, unresolved = [], [], []
    for kind, gfile, lineno, token, target, shape, ctx in sites:
        gabs = os.path.join(root, gfile)
        cand = []
        if target:
            t = target
            if not os.path.isabs(t):
                cand.append(os.path.normpath(os.path.join(os.path.dirname(gabs), t)))
                cand.append(os.path.normpath(os.path.join(root, t)))
            else:
                cand.append(t)
        tabs = next((c for c in cand if os.path.isfile(c)), None)
        selfgrep = False
        if tabs is None:
            unresolved.append((kind, gfile, lineno, token, target, shape, ctx))
            continue
        if os.path.normpath(tabs) == os.path.normpath(gabs):
            selfgrep = True
        prose, code = prose_code(tabs)
        if prose is None:
            unresolved.append((kind, gfile, lineno, token, target, shape, ctx))
            continue
        in_prose = token in prose
        in_code = token in code
        trel = os.path.relpath(tabs, root)
        rec = (kind, gfile, lineno, token, trel, shape, in_prose, in_code, selfgrep, ctx)
        if in_prose:
            holes.append(rec)
        else:
            clean.append(rec)

    resolved = len(holes) + len(clean)
    wired = [s for s in sites if s[6]]
    holes_wired = [h for h in holes if h[9]]
    clean_wired = [c for c in clean if c[9]]
    print("BOTH TERMS (P-67)")
    print("  TERM 1 -- literal-token-in-whole-file-source SITES ... %d" % len(sites))
    print("            ... WIRED TO A VERDICT, i.e. actual GUARDS   %d" % len(wired))
    print("            ... not wired (evidence dumps, generators)   %d"
          % (len(sites) - len(wired)))
    print("            ... target file resolved statically ....... %d" % resolved)
    print("            ... target NOT statically resolvable ...... %d  (counted, listed "
          "below -- P-40)" % len(unresolved))
    print("  TERM 2 -- resolved sites WITH THE SELF-MATCH HOLE .... %d" % len(holes))
    print("            ... of those, WIRED TO A VERDICT (real) ... %d" % len(holes_wired))
    print("            ... of those, token in prose ONLY ......... %d  (the assertion is "
          "satisfied by prose alone TODAY)"
          % len([h for h in holes if not h[7]]))
    print("            ... of those, the grep is SELF-directed ... %d"
          % len([h for h in holes if h[8]]))
    print("            resolved sites with NO prose occurrence ... %d (of which wired: %d)"
          % (len(clean), len(clean_wired)))
    print()
    print("  DENOMINATOR STATED PLAINLY (P-66/P-70): of %d resolvable-target source-grep "
          "sites, %d are wired to a verdict; %d of those %d have the hole. The other %d "
          "sites could not have their target resolved statically and are NOT a measured "
          "negative -- they are unmeasured, and counted as such."
          % (resolved, len(clean_wired) + len(holes_wired), len(holes_wired),
             len(clean_wired) + len(holes_wired), len(unresolved)))
    print()

    print("THE HOLES -- every one, with which file's prose supplies the token")
    if not holes:
        print("  (none)")
    for kind, gfile, lineno, token, trel, shape, in_prose, in_code, selfgrep, ctx in sorted(holes):
        sev = "PROSE-ONLY (the assertion is TRUE OF THE PROSE ALONE)" if not in_code \
            else "prose+code (code occurrence exists today; deleting it leaves the guard green)"
        print("  %s:%d  [%s]%s" % (gfile, lineno, kind, "  SELF-GREP" if selfgrep else ""))
        print("      token   %r" % token)
        print("      target  %s" % trel)
        print("      shape   %s" % shape)
        print("      wiring  %s" % (ctx or "NOT wired to a verdict (evidence dump, or a "
                                    "generator splicing a template) -- reported, not "
                                    "graded as a guard"))
        print("      verdict %s" % sev)
    print()

    print("TARGET NOT STATICALLY RESOLVABLE -- counted, not swept (P-40/P-66: this is a "
          "statement about the search)")
    if not unresolved:
        print("  (none)")
    for kind, gfile, lineno, token, target, shape, ctx in sorted(unresolved)[:40]:
        print("  %s:%d [%s] token=%r target-expr=%r" % (gfile, lineno, kind, token, target))
    if len(unresolved) > 40:
        print("  ... and %d more" % (len(unresolved) - 40))
    print()

    if unparsed:
        print("PYTHON FILES THAT WOULD NOT PARSE (%d) -- named, never silently dropped"
              % len(unparsed))
        for rel, err in unparsed:
            print("  %s: %s" % (rel, err))
        print()

    print("WHAT WAS SKIPPED, AND WHY (P-40)")
    print("  %5d non-instrument files (.md .json .txt .http .status .sql .sha256 ...) -- "
          "they contain no assertions." % len(other))
    print("  %5d Python file(s) that would not parse -- named above, not dropped silently."
          % len(unparsed))
    print("  %5d site(s) whose target expression is not static (a loop variable, an argv, "
          "a glob). The sweep cannot say what file they grade without executing them, so "
          "it says so instead of guessing." % len(unresolved))
    print("      Shell coverage is a REGEX over grep/git-grep/rg invocations with a "
          "quoted literal and a file operand; a pattern built in a variable, or a "
          "heredoc'd python -c, is NOT seen. Go coverage is a REGEX over "
          "strings.Contains(x, \"lit\") only.")
    print("      Routes OTHER than 'literal token in whole-file source' -- an AST guard "
          "with a wrong selector, a numeric threshold, a regex over a captured stdout -- "
          "are a different concept and are out of this sweep.")
    print()
    print("SCOPE OF REPAIR: T164's files_hint is .softhouse/capture/tierA-a2/ ONLY. Holes "
          "outside it are BACKLOG ITEMS reported here, not fixed.")
    print()
    print("SITES=%d RESOLVED=%d HOLES=%d UNRESOLVED=%d"
          % (len(sites), resolved, len(holes), len(unresolved)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
