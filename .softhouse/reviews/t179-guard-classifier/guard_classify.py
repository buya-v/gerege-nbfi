#!/usr/bin/env python3
"""T179 — a PARSER-based replacement for T156's regex guard-classifier.

WHY THIS EXISTS (P-48, in its purest form).
  T156's sweep (`.softhouse/capture/pathb/t149/t156-sweep-unguarded-mutators.py:58`)
  decided whether a mutating script protects itself with

      GUARD = re.compile(r"(?m)^[^#\\n]*(\\btrap\\b|\\bfinally\\s*:|atexit\\.register"
                         r"|__exit__|contextmanager)")

  i.e. by GREPPING SOURCE TEXT for the word `trap`.  `.softhouse/reviews/t47-probe/
  t47_edit_1.py` scored GUARDED on three occurrences of `trap`, all three inside
  string literals the script WRITES INTO the ratified DEC-1 ADR.  A file was scored
  safe by the prose it was writing, while rewriting a `user`-gated document in place
  with no handler on any exit path.

WHAT THIS TOOL CHANGES.
  1. Python is analysed with `ast`.  A guard is a NODE — `ast.Try` with a `finalbody`,
     an `atexit.register` / `signal.signal` call, or a restoring context manager — and
     it must be REACHABLE FROM THE MUTATION SITE (an enclosing node on the site's own
     ancestor chain, or a whole-process handler that is reachable from module
     execution).  A `try/finally` in another function no longer launders a mutation.
  2. The TARGET of a mutation is read off the mutating call's own ARGUMENT
     EXPRESSION, not off whole-file text.  T156 matched its TARGET regexes anywhere in
     the file, so a script that merely mentioned `.softhouse/vectors` in a comment was
     scored as mutating the vector store.
  3. `SANDBOX` is likewise decided per-site: T156's `SANDBOXY` regex matched
     `tempfile.`/`/tmp/` anywhere in the file and then excused the whole file.
  4. Shell is REFUSED, not guessed — see `classify_shell()`.  The refusals are counted
     in the population table and are a first-class outcome, never a silent skip (P-40).

WHAT THIS TOOL STILL CANNOT DO — read this before quoting its numbers.
  * It cannot classify shell at all (no shell parser in the stdlib; `bashlex` is not
    installed here — checked at runtime and printed).  Every `.sh` file is REFUSED.
  * `GUARDED-PROCESS` means a handler is registered and reachable.  It does NOT mean
    the handler restores THIS artefact; nothing here reads the handler's body for
    intent, and a registration that runs AFTER the mutation is indistinguishable from
    one that runs before by static order alone.  Treat it as "a handler exists on this
    path", i.e. weaker than `GUARDED-FINALLY`.
  * Name resolution is module-level constants only (`X = "lit"`, `os.path.join(...)`
    of resolvable parts, f-string constant parts).  A target computed at runtime, or
    passed in as a parameter, resolves to `UNKNOWN` — and `UNKNOWN` is REPORTED as its
    own scope, never folded into "not a trusted target".
  * Cross-file call graphs are out of scope.  A mutation performed by a helper in
    another module is invisible.
  * `subprocess`/`os.system` argv is inspected only when it is a literal list or a
    literal string; a command assembled at runtime is `UNKNOWN`.
  * It reads only what is on disk at the path given.  It is not a git-aware tool.

Exit codes:
  0  sweep completed (report mode), or completed with no UNGUARDED trusted-target site
     (--enforce)
  1  --enforce and at least one UNGUARDED site on a TRUSTED target
  2  usage error
  3  ZERO files inspected — an error, never a pass (P-35)
"""

import argparse
import ast
import json
import os
import re
import sys
import tempfile

# --------------------------------------------------------------------------
# Verdicts.  Ordered worst-first for file-level roll-up.
# --------------------------------------------------------------------------
UNGUARDED = "UNGUARDED"
GUARDED_FINALLY = "GUARDED-FINALLY"
GUARDED_CM = "GUARDED-CONTEXTMANAGER"
GUARDED_INDIRECT = "GUARDED-FINALLY-INDIRECT"
GUARDED_PROCESS = "GUARDED-PROCESS"
ATOMIC = "ATOMIC"
SANDBOX = "SANDBOX"

VERDICT_ORDER = [UNGUARDED, GUARDED_PROCESS, GUARDED_INDIRECT, GUARDED_CM,
                 GUARDED_FINALLY, ATOMIC, SANDBOX]
GUARDING = {GUARDED_FINALLY, GUARDED_CM, GUARDED_INDIRECT, GUARDED_PROCESS}

# Scopes for the mutation TARGET, decided per call site.
TRUSTED = "TRUSTED"        # an artefact a later reader treats as ground truth
UNKNOWN = "UNKNOWN"        # could not resolve the target expression — reported, not dropped
SCRATCH = "SCRATCH"        # provably a temp/sandbox path

# Refusal reasons (files we decline to classify).  Counted, never silent.
REFUSE_SHELL = "REFUSED-SHELL-NO-PARSER"
REFUSE_SYNTAX = "REFUSED-PYTHON-SYNTAXERROR"
REFUSE_DECODE = "REFUSED-UNREADABLE"

# --------------------------------------------------------------------------
# Target classification.  Same four buckets T156 used, so the two sweeps are
# comparable — but applied to the AST-extracted argument expression of the
# mutating call, not to the whole file.
# --------------------------------------------------------------------------
TARGET_RX = [
    ("STORE", re.compile(r"\.softhouse/vectors|STORE_ROOT|/vectors/")),
    ("PORT", re.compile(r"nexus/internal|\.go\b")),
    ("CAPTURE", re.compile(r"\.softhouse/capture|/out/|capture_dir|OUTDIR")),
    ("RIG", re.compile(r"attest\.py|conformance\.sh|contract\.go|PIN\.json|"
                       r"capabilities\.json")),
    ("ADR", re.compile(r"docs/adr|DEC-\d")),
    ("PATTERNS", re.compile(r"patterns\.md|program\.json|tasks\.json|gates\.md|"
                            r"obligations\.md|reference-oracle\.md")),
]
SCRATCH_RX = re.compile(r"tempfile\.|mkdtemp|mkstemp|TemporaryDirectory|"
                        r"NamedTemporaryFile|TMPDIR|(?<![\w.])/tmp/|/var/folders/|"
                        r"\bscratch\b|\btmpdir\b|\btmp_?dir\b", re.I)

# --------------------------------------------------------------------------
# Mutating calls.
# --------------------------------------------------------------------------
# name -> index of the positional argument that names the TARGET being mutated
OS_MUTATORS = {
    "os.replace": 1, "os.rename": 1, "os.remove": 0, "os.unlink": 0,
    "os.rmdir": 0, "os.truncate": 0, "os.chmod": 0, "os.removedirs": 0,
    "shutil.move": 1, "shutil.copy": 1, "shutil.copy2": 1, "shutil.copyfile": 1,
    "shutil.copytree": 1, "shutil.rmtree": 0, "shutil.chown": 0,
}
OPENERS = {"open", "io.open", "codecs.open", "gzip.open"}
# Path methods that mutate the RECEIVER.
PATH_SELF_METHODS = {"write_text", "write_bytes", "unlink", "rmdir", "touch",
                     "mkdir", "chmod"}
# Path methods that mutate the ARGUMENT (`Path(tmp).replace(target)`), and are
# atomic when the receiver is a temp file.  Required to take exactly one positional
# argument and no keywords, which is what separates `Path.replace(dst)` from
# `str.replace(old, new)` — the false friend that made an earlier draft of this tool
# report string substitutions as file mutations.
PATH_DEST_METHODS = {"replace", "rename"}
SUBPROCESS_RUNNERS = {"subprocess.run", "subprocess.call", "subprocess.check_call",
                      "subprocess.check_output", "subprocess.Popen"}
SH_MUTATING_ARGV = re.compile(
    r"(?<![\w./-])(mv|cp|rm|install|truncate|ln|tee|dd|chmod)(?![\w-])|"
    r"sed\s+(-[a-zA-Z]*\s+)*-i|"
    r"git\s+(checkout\s+--|restore|stash)|"
    r">\s*\S")

RESTORING_CM_NAMES = {"contextlib.ExitStack", "ExitStack",
                      "contextlib.AsyncExitStack", "AsyncExitStack"}


def dotted(node):
    """Dotted name of an AST expression, '' if it is not a plain name/attribute."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted(node.value)
        return base + "." + node.attr if base else node.attr
    return ""


def unparse(node):
    try:
        return ast.unparse(node)
    except Exception:                                       # pragma: no cover
        return "<unparse-unavailable>"


class ConstResolver:
    """Module-level string constants, so `open(STORE_PATH, 'w')` can be scoped.

    Deliberately shallow: literals, `os.path.join` of resolvable parts, `+` of
    resolvable parts, f-string constant fragments.  Anything else -> None, and the
    site is reported as UNKNOWN rather than guessed at.
    """

    TEMP_CALLS = ("tempfile.mkstemp", "tempfile.mkdtemp", "tempfile.NamedTemporaryFile",
                  "tempfile.TemporaryDirectory", "mkstemp", "mkdtemp",
                  "NamedTemporaryFile", "TemporaryDirectory")

    def __init__(self, tree):
        self.consts = {}
        # Names bound to a temp path — `fd, tmp = tempfile.mkstemp(...)` is a tuple
        # assignment, so a literal resolver alone would miss it and then score an
        # atomic `os.replace(tmp, target)` as an unguarded write.
        self.scratch_names = set()
        # PARTIAL expansion: `DOC = os.path.join(W, "docs/adr/DEC-1-....md")` does not
        # resolve (W comes from __file__), but the literal fragments of its assigned
        # expression are still evidence about what DOC names.  Name -> those fragments.
        # Name-based and NOT scope-aware (first assignment wins), so it can mis-attribute
        # a name reused in two functions; it only ever affects the reported SCOPE tag,
        # never the guard verdict, and every site prints its target expression so a
        # reader can adjudicate.
        self.partial = {}
        for stmt in ast.walk(tree):
            if not isinstance(stmt, ast.Assign):
                continue
            if len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                v = self.resolve(stmt.value)
                if v is not None:
                    self.consts.setdefault(stmt.targets[0].id, v)
                else:
                    frags = [n.value for n in ast.walk(stmt.value)
                             if isinstance(n, ast.Constant)
                             and isinstance(n.value, str)]
                    if frags:
                        self.partial.setdefault(stmt.targets[0].id, "/".join(frags))
            is_temp = isinstance(stmt.value, ast.Call) and \
                dotted(stmt.value.func) in self.TEMP_CALLS
            if not is_temp:
                v = self.resolve(stmt.value)
                is_temp = bool(v and SCRATCH_RX.search(v))
            if not is_temp:
                # `scratch = "/tmp/t61cf-" + tag` does not RESOLVE (tag is runtime),
                # but the literal fragment "/tmp/…" is decisive on its own.  Without
                # this, a /tmp tree that mirrors the repo was scored TRUSTED —
                # measured on .softhouse/capture/t61-halfeven/src/run-counterfactuals.py.
                is_temp = any(isinstance(n, ast.Constant) and
                              isinstance(n.value, str) and SCRATCH_RX.search(n.value)
                              for n in ast.walk(stmt.value))
            if is_temp:
                for tgt in stmt.targets:
                    for n in ast.walk(tgt):
                        if isinstance(n, ast.Name):
                            self.scratch_names.add(n.id)
        # `with tempfile.TemporaryDirectory() as tmp:` binds tmp through a withitem,
        # not an Assign — missed by the loop above, and it is the commonest sandbox
        # idiom in this repo.  A selftest rig that builds `<tmp>/.softhouse/capture/...`
        # was scored TRUSTED until this was added.
        for n in ast.walk(tree):
            if isinstance(n, (ast.With, ast.AsyncWith)):
                for item in n.items:
                    ctx = item.context_expr
                    if isinstance(ctx, ast.Call) and \
                            dotted(ctx.func) in self.TEMP_CALLS and \
                            item.optional_vars is not None:
                        for v in ast.walk(item.optional_vars):
                            if isinstance(v, ast.Name):
                                self.scratch_names.add(v.id)
        # Transitive: `sb = mkdtemp(); t149 = os.path.join(sb, ".softhouse/capture/…")`
        # — t149 LOOKS like a trusted capture path and is in fact inside a sandbox.
        # Without this, a scratch tree that mirrors the repo layout is scored TRUSTED.
        # Iterate to a fixpoint; the assignment graph is tiny.
        assigns = [st for st in ast.walk(tree) if isinstance(st, ast.Assign)]
        for _ in range(6):
            grew = False
            for stmt in assigns:
                refs = {n.id for n in ast.walk(stmt.value) if isinstance(n, ast.Name)}
                if not (refs & self.scratch_names):
                    continue
                for tgt in stmt.targets:
                    for n in ast.walk(tgt):
                        if isinstance(n, ast.Name) and n.id not in self.scratch_names:
                            self.scratch_names.add(n.id)
                            grew = True
            if not grew:
                break

    def resolve(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name):
            return self.consts.get(node.id)
        if isinstance(node, ast.JoinedStr):
            parts = []
            for v in node.values:
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    parts.append(v.value)
                else:
                    inner = self.resolve(v.value) if isinstance(v, ast.FormattedValue) \
                        else None
                    parts.append(inner if inner is not None else "{}")
            return "".join(parts)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            a, b = self.resolve(node.left), self.resolve(node.right)
            if a is not None and b is not None:
                return a + b
            return None
        if isinstance(node, ast.Call):
            name = dotted(node.func)
            if name in ("os.path.join", "posixpath.join", "Path", "pathlib.Path"):
                parts = [self.resolve(a) for a in node.args]
                if all(p is not None for p in parts):
                    return "/".join(p.strip("/") if i else p
                                    for i, p in enumerate(parts))
            if name in ("os.path.abspath", "os.path.dirname", "os.path.realpath",
                        "str", "os.fspath"):
                if node.args:
                    return self.resolve(node.args[0])
        return None

    def probe(self, node):
        """(resolved_or_None, text_probe).

        The text probe is built from the ARGUMENT SUBTREE only — every string
        constant inside it plus its unparsed form — never from whole-file source.
        """
        resolved = self.resolve(node)
        pieces = [unparse(node)]
        for n in ast.walk(node):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                pieces.append(n.value)
            elif isinstance(n, ast.Name) and n.id in self.consts:
                pieces.append(self.consts[n.id])
            elif isinstance(n, ast.Name) and n.id in self.scratch_names:
                pieces.append("tempfile.")   # marks the subtree as scratch-derived
            elif isinstance(n, ast.Name) and n.id in self.partial:
                pieces.append(self.partial[n.id])
        if resolved:
            pieces.append(resolved)
        return resolved, "\n".join(pieces)


def scope_of(probe_text):
    tags = [name for name, rx in TARGET_RX if rx.search(probe_text)]
    if SCRATCH_RX.search(probe_text):
        return SCRATCH, tags
    if tags:
        return TRUSTED, tags
    return UNKNOWN, []


# --------------------------------------------------------------------------
# Guard reachability
# --------------------------------------------------------------------------
def parent_map(tree):
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    return parents


def ancestors(node, parents):
    chain = []
    cur = parents.get(node)
    while cur is not None:
        chain.append(cur)
        cur = parents.get(cur)
    return chain


def enclosing_try_finally(node, parents):
    """The nearest ancestor `try:` WITH a `finally:` that actually covers `node`.

    A node sitting in the `finalbody` itself is NOT covered by that finally.
    """
    child = node
    cur = parents.get(node)
    while cur is not None:
        if isinstance(cur, ast.Try) and cur.finalbody:
            if not _in_body(child, cur.finalbody):
                return cur
        child = cur
        cur = parents.get(cur)
    return None


def _in_body(child, body):
    return any(child is stmt or child in set(ast.walk(stmt)) for stmt in body)


def enclosing_restoring_with(node, parents, local_cms):
    cur = parents.get(node)
    while cur is not None:
        if isinstance(cur, (ast.With, ast.AsyncWith)):
            for item in cur.items:
                ctx = item.context_expr
                name = dotted(ctx.func) if isinstance(ctx, ast.Call) else dotted(ctx)
                if name in RESTORING_CM_NAMES or name in local_cms:
                    return cur, name
        cur = parents.get(cur)
    return None, None


def local_restoring_cms(tree):
    """Context managers DEFINED IN THIS FILE that plausibly restore state:
    a @contextlib.contextmanager generator whose body contains a `try:` with a
    `finally:`, or a class with an `__exit__` method."""
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            decs = {dotted(d.func) if isinstance(d, ast.Call) else dotted(d)
                    for d in n.decorator_list}
            if decs & {"contextlib.contextmanager", "contextmanager",
                       "contextlib.asynccontextmanager", "asynccontextmanager"}:
                if any(isinstance(x, ast.Try) and x.finalbody for x in ast.walk(n)):
                    out.add(n.name)
        if isinstance(n, ast.ClassDef):
            if any(isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and
                   m.name in ("__exit__", "__aexit__") for m in n.body):
                out.add(n.name)
    return out


def enclosing_func(node, parents):
    cur = parents.get(node)
    while cur is not None:
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return cur
        cur = parents.get(cur)
    return None


def module_reachable_funcs(tree, parents):
    """Functions reachable from module execution (module body statements that are
    not defs/imports, plus any `if __name__ == '__main__':` block), by intra-file
    call graph.  Used only to decide whether a registered atexit/signal handler is
    on a live path."""
    funcs = {n.name: n for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    seeds = []
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                             ast.Import, ast.ImportFrom)):
            continue
        seeds.append(stmt)
    reachable, queue = set(), []
    for stmt in seeds:
        for n in ast.walk(stmt):
            if isinstance(n, ast.Call):
                nm = dotted(n.func).split(".")[-1]
                if nm in funcs:
                    queue.append(nm)
    while queue:
        nm = queue.pop()
        if nm in reachable:
            continue
        reachable.add(nm)
        for n in ast.walk(funcs[nm]):
            if isinstance(n, ast.Call):
                sub = dotted(n.func).split(".")[-1]
                if sub in funcs and sub not in reachable:
                    queue.append(sub)
    return reachable, funcs, seeds


def process_handlers(tree, parents, reachable, seeds):
    """atexit.register / signal.signal call nodes that are on a module-live path."""
    live = []
    seed_nodes = set()
    for stmt in seeds:
        seed_nodes.update(ast.walk(stmt))
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        name = dotted(n.func)
        if name not in ("atexit.register", "signal.signal", "signal.sigaction"):
            continue
        fn = enclosing_func(n, parents)
        if fn is None:
            live.append((name, n.lineno, "module-scope"))
        elif n in seed_nodes:
            live.append((name, n.lineno, "module-scope"))
        elif fn.name in reachable:
            live.append((name, n.lineno, "in %s() [module-reachable]" % fn.name))
        # A registration inside a function nothing calls is NOT live; it is dropped
        # here on purpose, and shows up as an UNGUARDED site rather than as a guard.
    return live


def indirectly_guarded_funcs(tree, parents):
    """Functions whose EVERY intra-file call site sits inside a try/finally.

    This is the one interprocedural step taken, and it is deliberately conservative:
    one un-guarded call site disqualifies the function.  A function with zero
    in-file call sites is NOT considered guarded.
    """
    funcs = {n.name for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    sites = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            nm = dotted(n.func).split(".")[-1]
            if nm in funcs:
                sites.setdefault(nm, []).append(
                    enclosing_try_finally(n, parents) is not None)
    return {nm for nm, flags in sites.items() if flags and all(flags)}


# --------------------------------------------------------------------------
# Mutation-site extraction
# --------------------------------------------------------------------------
def _open_mode(call):
    mode = ""
    if len(call.args) > 1 and isinstance(call.args[1], ast.Constant):
        mode = str(call.args[1].value)
    for kw in call.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
            mode = str(kw.value.value)
    return mode


def mutation_sites(tree, resolver):
    """Every mutating call NODE, with the argument expression that names its target."""
    out = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        name = dotted(n.func)

        if name in OS_MUTATORS:
            idx = OS_MUTATORS[name]
            tgt = n.args[idx] if len(n.args) > idx else None
            src = n.args[0] if n.args else None
            out.append({"node": n, "verb": name, "target_node": tgt,
                        "source_node": src if idx == 1 else None})
            continue

        if name in OPENERS:
            mode = _open_mode(n)
            if any(c in mode for c in "wax+"):
                out.append({"node": n, "verb": "%s(mode=%r)" % (name, mode),
                            "target_node": n.args[0] if n.args else None,
                            "source_node": None})
            continue

        if isinstance(n.func, ast.Attribute) and n.func.attr in PATH_SELF_METHODS:
            out.append({"node": n, "verb": "Path.%s" % n.func.attr,
                        "target_node": n.func.value, "source_node": None})
            continue

        if isinstance(n.func, ast.Attribute) and n.func.attr in PATH_DEST_METHODS:
            if len(n.args) == 1 and not n.keywords:
                out.append({"node": n, "verb": "Path.%s" % n.func.attr,
                            "target_node": n.args[0],
                            "source_node": n.func.value})
            continue

        if name in SUBPROCESS_RUNNERS or name in ("os.system", "os.popen"):
            argv_text = None
            if n.args:
                resolved, probe = resolver.probe(n.args[0])
                argv_text = probe
            if argv_text and SH_MUTATING_ARGV.search(argv_text):
                out.append({"node": n, "verb": "%s(shell)" % name,
                            "target_node": n.args[0], "source_node": None})
            continue
    return out


# --------------------------------------------------------------------------
# Per-file classification
# --------------------------------------------------------------------------
def classify_python(rel, src):
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return {"path": rel, "lang": "python", "refused": REFUSE_SYNTAX,
                "detail": "%s at line %s" % (e.msg, e.lineno), "sites": []}

    parents = parent_map(tree)
    resolver = ConstResolver(tree)
    local_cms = local_restoring_cms(tree)
    reachable, _funcs, seeds = module_reachable_funcs(tree, parents)
    handlers = process_handlers(tree, parents, reachable, seeds)
    indirect = indirectly_guarded_funcs(tree, parents)

    # P-48 instrumentation: how many guard WORDS live in string literals?  This is
    # what T156's regex was actually counting.  Reported, never used to classify.
    literal_guard_words = 0
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            low = n.value.lower()
            for w in ("trap", "finally", "atexit", "__exit__", "contextmanager"):
                literal_guard_words += low.count(w)

    sites = []
    for m in mutation_sites(tree, resolver):
        node = m["node"]
        if m["target_node"] is None:
            scope, tags, target_text = UNKNOWN, [], "<no target argument>"
        else:
            resolved, probe = resolver.probe(m["target_node"])
            scope, tags = scope_of(probe)
            target_text = unparse(m["target_node"])[:120]

        verdict, why = UNGUARDED, "no try/finally, context manager or live handler " \
                                  "encloses this call"

        # ATOMIC beats everything: os.replace of a temp file needs no handler at all.
        if m["verb"] in ("os.replace", "os.rename", "Path.replace",
                         "Path.rename") and m["source_node"] is not None:
            _r, sprobe = resolver.probe(m["source_node"])
            if SCRATCH_RX.search(sprobe):
                verdict, why = ATOMIC, "os.replace() of a temp file — atomic on POSIX"

        if verdict == UNGUARDED and scope == SCRATCH:
            verdict, why = SANDBOX, "target resolves to a temp/scratch path"

        if verdict == UNGUARDED:
            t = enclosing_try_finally(node, parents)
            if t is not None:
                verdict = GUARDED_FINALLY
                why = "enclosed by try/finally at line %d" % t.lineno
        if verdict == UNGUARDED:
            w, nm = enclosing_restoring_with(node, parents, local_cms)
            if w is not None:
                verdict = GUARDED_CM
                why = "enclosed by `with %s` at line %d (restoring CM)" % (nm, w.lineno)
        if verdict == UNGUARDED:
            fn = enclosing_func(node, parents)
            if fn is not None and fn.name in indirect:
                verdict = GUARDED_INDIRECT
                why = "every in-file call of %s() is inside a try/finally" % fn.name
        if verdict == UNGUARDED and handlers:
            verdict = GUARDED_PROCESS
            why = "live process handler: " + "; ".join(
                "%s@%d (%s)" % (h[0], h[1], h[2]) for h in handlers[:3])

        sites.append({"line": node.lineno, "verb": m["verb"], "scope": scope,
                      "target_tags": tags, "target": target_text,
                      "verdict": verdict, "why": why})

    n_try_finally = len([n for n in ast.walk(tree)
                         if isinstance(n, ast.Try) and n.finalbody])
    return {"path": rel, "lang": "python", "refused": None, "sites": sites,
            "literal_guard_words": literal_guard_words,
            "live_handlers": [[h[0], h[1], h[2]] for h in handlers],
            "try_finally_nodes": n_try_finally,
            "restoring_cms": sorted(local_cms),
            # The direct answer to "does this file contain ANY real guard node?",
            # independent of whether any mutation is reachable from it.  This is the
            # number T156's GUARD regex was pretending to report.
            "guard_nodes": n_try_finally + len(handlers) + len(local_cms)}


SHELL_PARSER = None
try:                                                        # pragma: no cover
    import bashlex                                          # noqa: F401
    SHELL_PARSER = "bashlex"
except Exception:
    SHELL_PARSER = None


def classify_shell(rel, src):
    """DOCUMENTED REFUSAL.

    There is no shell parser in the Python standard library, and `bashlex` is not
    installed in this environment (checked at import time; the result is printed in
    the header of every run).  `shlex` is a tokeniser, not a parser: it strips quotes
    and comments — better than a grep — but it cannot tell a `trap` that is *executed*
    from a `trap` inside a here-doc, a function that is never called, or a subshell,
    and it cannot decide reachability at all.

    So this classifier REFUSES every shell file, and the refusals are COUNTED in the
    population table.  A wrong classification of a shell script is exactly the defect
    T179 exists to remove; a counted refusal is not.
    """
    return {"path": rel, "lang": "shell", "refused": REFUSE_SHELL,
            "detail": "no shell parser available (bashlex not installed); "
                      "shlex is a tokeniser, not a parser — refusing rather than "
                      "guessing", "sites": [],
            "bytes": len(src)}


def classify_path(path, rel=None):
    rel = rel or path
    try:
        with open(path, "r", encoding="utf-8", errors="strict") as f:
            src = f.read()
    except (OSError, UnicodeDecodeError) as e:
        return {"path": rel, "lang": "?", "refused": REFUSE_DECODE,
                "detail": type(e).__name__, "sites": []}
    if path.endswith(".py"):
        return classify_python(rel, src)
    if path.endswith(".sh") or path.endswith(".bash"):
        return classify_shell(rel, src)
    return {"path": rel, "lang": "?", "refused": "NOT-A-SCRIPT", "sites": []}


def file_verdict(res):
    """Worst site verdict on a TRUSTED or UNKNOWN target; None if no sites."""
    if res.get("refused"):
        return res["refused"]
    if not res["sites"]:
        return None
    ranked = sorted(res["sites"], key=lambda s: VERDICT_ORDER.index(s["verdict"]))
    return ranked[0]["verdict"]


# --------------------------------------------------------------------------
# Sweep
# --------------------------------------------------------------------------
def sweep(root, excludes):
    files, other_ext, excluded = [], {}, []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in sorted(filenames):
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, root)
            if any(x in p for x in excludes):
                excluded.append(rel)
                continue
            if fn.endswith((".py", ".sh", ".bash")):
                files.append(p)
            else:
                ext = os.path.splitext(fn)[1] or "<none>"
                other_ext[ext] = other_ext.get(ext, 0) + 1
    files.sort()
    results = [classify_path(p, os.path.relpath(p, root)) for p in files]
    return results, other_ext, excluded


def report(results, other_ext, excluded, root, out=sys.stdout):
    w = out.write
    w("=== T179 parser-based guard classifier\n")
    w("root                : %s\n" % root)
    w("python parser       : ast (stdlib, authoritative for Python)\n")
    w("shell parser        : %s\n" % (SHELL_PARSER or
                                      "NONE — every .sh file is REFUSED, and counted"))
    w("\n")

    py = [r for r in results if r["lang"] == "python" and not r["refused"]]
    refused = [r for r in results if r["refused"]]
    n_sites = sum(len(r["sites"]) for r in py)

    if not results:
        w("ERROR: zero files inspected. That is an error, not a pass (P-35).\n")
        return 3

    w("--- POPULATION, with denominators\n")
    w("  script files enumerated (.py/.sh/.bash)   : %d\n" % len(results))
    w("    of which Python, parsed                 : %d\n" % len(py))
    w("    of which REFUSED                        : %d\n" % len(refused))
    for reason in (REFUSE_SHELL, REFUSE_SYNTAX, REFUSE_DECODE):
        n = len([r for r in refused if r["refused"] == reason])
        if n:
            w("      %-38s: %d\n" % (reason, n))
    w("  non-script files under the same root      : %d (never inspected)\n"
      % sum(other_ext.values()))
    w("    largest uninspected groups              : %s\n"
      % ", ".join("%s %d" % (e, n) for e, n in
                  sorted(other_ext.items(), key=lambda t: -t[1])[:6]))
    if excluded:
        w("  explicitly excluded by --exclude          : %d (%s%s)\n"
          % (len(excluded), ", ".join(excluded[:4]),
             ", …" if len(excluded) > 4 else ""))
    w("  mutation call sites found in Python       : %d\n" % n_sites)
    w("\n")

    # scope x verdict matrix — nothing is dropped
    w("--- MUTATION SITES: scope x verdict (every site appears exactly once)\n")
    matrix = {}
    for r in py:
        for s in r["sites"]:
            matrix[(s["scope"], s["verdict"])] = \
                matrix.get((s["scope"], s["verdict"]), 0) + 1
    w("  %-10s %s\n" % ("scope", "".join("%-26s" % v for v in VERDICT_ORDER)))
    for scope in (TRUSTED, UNKNOWN, SCRATCH):
        row = [matrix.get((scope, v), 0) for v in VERDICT_ORDER]
        w("  %-10s %s   (total %d)\n"
          % (scope, "".join("%-26d" % n for n in row), sum(row)))
    tot = sum(matrix.values())
    w("  %-10s %s   (total %d)\n"
      % ("ALL", "".join("%-26d" % sum(matrix.get((sc, v), 0)
                                      for sc in (TRUSTED, UNKNOWN, SCRATCH))
                        for v in VERDICT_ORDER), tot))
    if tot != n_sites:
        w("  TALLY DOES NOT CLOSE: %d != %d — treat this run as broken\n"
          % (tot, n_sites))
    w("\n")

    trusted_unguarded = [(r, s) for r in py for s in r["sites"]
                         if s["scope"] == TRUSTED and s["verdict"] == UNGUARDED]
    w("--- UNGUARDED MUTATIONS OF A TRUSTED ARTEFACT (%d sites in %d files)\n"
      % (len(trusted_unguarded),
         len({r["path"] for r, _ in trusted_unguarded})))
    for r, s in trusted_unguarded:
        w("  %s:%d  %s  tags=%s\n      target: %s\n"
          % (r["path"], s["line"], s["verb"], ",".join(s["target_tags"]), s["target"]))
    w("\n")

    unknown_unguarded = [(r, s) for r in py for s in r["sites"]
                         if s["scope"] == UNKNOWN and s["verdict"] == UNGUARDED]
    w("--- UNGUARDED MUTATIONS WHOSE TARGET COULD NOT BE RESOLVED (%d sites in %d "
      "files)\n" % (len(unknown_unguarded),
                    len({r["path"] for r, _ in unknown_unguarded})))
    w("    These are NOT clean and NOT dirty. They are unresolved, and they are\n"
      "    printed so nothing is silently dropped (P-40).\n")
    for r, s in unknown_unguarded[:400]:
        w("  %s:%d  %s   target: %s\n" % (r["path"], s["line"], s["verb"], s["target"]))
    w("\n")

    # P-48 detector: files whose guard WORDS live only in string literals.
    w("--- P-48 DETECTOR: files T156's regex would score GUARDED on prose alone\n")
    w("    (guard words present ONLY inside string literals; zero try/finally nodes)\n")
    n_p48 = 0
    for r in py:
        if r.get("literal_guard_words") and not r.get("try_finally_nodes") and \
                not r.get("live_handlers") and r["sites"]:
            n_p48 += 1
            w("  %-64s guard-words-in-literals=%d  sites=%d\n"
              % (r["path"], r["literal_guard_words"], len(r["sites"])))
    if not n_p48:
        w("  none in this root\n")
    w("\n")

    w("--- REFUSED FILES, NAMED (a refusal is an outcome, not a skip)\n")
    for r in refused:
        w("  %-64s %s\n" % (r["path"], r["refused"]))
    w("  refused total: %d\n" % len(refused))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=None,
                    help="directory to sweep (default: the repo's .softhouse/)")
    ap.add_argument("--exclude", action="append", default=[],
                    help="substring of a path to exclude; counted and named")
    ap.add_argument("--json", default=None, help="write full results as JSON")
    ap.add_argument("--enforce", action="store_true",
                    help="exit 1 if any TRUSTED-target site is UNGUARDED")
    ap.add_argument("--file", action="append", default=[],
                    help="classify these files only (no sweep)")
    args = ap.parse_args(argv)

    if args.file:
        results = [classify_path(os.path.abspath(p), p) for p in args.file]
        other_ext, excluded, root = {}, [], "<explicit file list>"
    else:
        root = args.root
        if root is None:
            here = os.path.dirname(os.path.abspath(__file__))
            root = os.path.abspath(os.path.join(here, "..", ".."))
        root = os.path.abspath(root)
        if not os.path.isdir(root):
            sys.stderr.write("no such root: %s\n" % root)
            return 2
        results, other_ext, excluded = sweep(root, args.exclude)

    if not results:
        sys.stderr.write("ERROR: zero files inspected — an error, not a pass (P-35)\n")
        return 3

    rc = report(results, other_ext, excluded, root)
    if rc:
        return rc

    if args.json:
        # This tool's own only write.  Done atomically (mkstemp in the target's own
        # directory + os.replace) so that this file's verdict under its own
        # classifier is ATOMIC and not UNGUARDED — P-48 rule 4, and a measuring
        # instrument that fails its own measurement is not one worth quoting.
        d = os.path.dirname(os.path.abspath(args.json)) or "."
        fd, tmp = tempfile.mkstemp(dir=d, prefix=".t179-json-")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=1, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, args.json)

    if args.enforce:
        bad = [(r["path"], s) for r in results for s in r.get("sites", [])
               if s["scope"] == TRUSTED and s["verdict"] == UNGUARDED]
        if bad:
            sys.stderr.write("ENFORCE: %d unguarded mutation(s) of a trusted "
                             "artefact\n" % len(bad))
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
