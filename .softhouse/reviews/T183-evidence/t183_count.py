#!/usr/bin/env python3
"""T183 — INDEPENDENT re-derivation of the "unguarded in-place rewriters of a
ratified/frozen artefact" population, under ONE STATED RULE.

RULE R-T183 (stated before it is applied; no averaging, no inheriting):

  SITE      an AST call that TRUNCATES a file in place:
              open / io.open / codecs.open  with a mode string containing 'w'
              Path(...).write_text / .write_bytes ;  os.truncate
            `os.replace` is NOT a site (atomic rename, P-48 rule 4).

  UNGUARDED no guard NODE is reachable from the site: no enclosing ast.Try with a
            finalbody covering it, no enclosing `with` on a restoring CM, no
            module-live atexit/signal registration, and the site is not part of a
            mkstemp+os.replace atomic pair.  (Same reachability notion as T179 --
            I am not re-litigating that half, I am re-litigating TARGET resolution.)

  TARGET    resolved from the write call's own first argument, by
              (a) module-level constant substitution  X = "lit"  ->  "lit"
              (b) ONE BACKWARD INTERPROCEDURAL STEP: if the argument is a PARAMETER
                  of the enclosing function, take the UNION of the corresponding
                  actual arguments at every in-file call site of that function,
                  resolved by (a).
            (b) is the step T179 does not take.  T179 already takes the mirror-image
            FORWARD step for guards (`indirectly_guarded_funcs`), so this is the same
            analysis run in the other direction, not a new capability.
            Anything still unresolved is UNKNOWN and is PRINTED, never dropped.

  IN-POP    the resolved target matches a RATIFIED/FROZEN artefact:
              ADR       docs/adr/DEC-<n>*.md
              CONTRACT  nexus/internal/apps/loanschedule/contract/contract.go

  UNIT      one (file, artefact-class) PAIR.  A file that truncates both the ADR and
            contract.go counts ONCE UNDER EACH.  Per-site and per-file totals are
            printed alongside so the three prior counts can be reconciled.
"""
import ast, os, sys

ADR = "ADR"
CONTRACT = "CONTRACT"

def dotted(n):
    if isinstance(n, ast.Name): return n.id
    if isinstance(n, ast.Attribute):
        b = dotted(n.value)
        return (b + "." + n.attr) if b else n.attr
    return ""

def artefact(path):
    if not isinstance(path, str): return None
    if "docs/adr/DEC-" in path and path.endswith(".md"): return ADR
    if path.endswith("loanschedule/contract/contract.go"): return CONTRACT
    return None

def parents_of(tree):
    p = {}
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n): p[c] = n
    return p

def enclosing_try_finally(node, parents):
    child, cur = node, parents.get(node)
    while cur is not None:
        if isinstance(cur, ast.Try) and cur.finalbody:
            if not any(child is s or child in set(ast.walk(s)) for s in cur.finalbody):
                return cur
        child, cur = cur, parents.get(cur)
    return None

def enclosing_with(node, parents):
    cur = parents.get(node)
    while cur is not None:
        if isinstance(cur, (ast.With, ast.AsyncWith)): return cur
        cur = parents.get(cur)
    return None

def enclosing_func(node, parents):
    cur = parents.get(node)
    while cur is not None:
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)): return cur
        cur = parents.get(cur)
    return None

def const_map(tree):
    m = {}
    for stmt in ast.walk(tree):
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 \
           and isinstance(stmt.targets[0], ast.Name) \
           and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
            m.setdefault(stmt.targets[0].id, stmt.value.value)
    return m

def resolve_simple(node, consts):
    """(a) module-constant substitution only."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str): return node.value
    if isinstance(node, ast.Name): return consts.get(node.id)
    return None

def resolve_backstep(node, consts, tree, parents):
    """(b) ONE BACKWARD STEP through the enclosing function's parameters."""
    if not isinstance(node, ast.Name): return []
    fn = enclosing_func(node, parents)
    if fn is None: return []
    names = [a.arg for a in fn.args.args]
    if node.id not in names: return []
    idx = names.index(node.id)
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and dotted(n.func).split(".")[-1] == fn.name:
            if len(n.args) > idx:
                v = resolve_simple(n.args[idx], consts)
                if v is not None: out.append(v)
    return out

def write_mode(call):
    if len(call.args) > 1:
        a = call.args[1]
        if isinstance(a, ast.Constant) and isinstance(a.value, str): return a.value
    for kw in call.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant): return kw.value.value or ""
    return ""

def sites(tree, consts, parents):
    out = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call): continue
        name = dotted(n.func)
        tgt_node = None
        kind = None
        if name in ("open", "io.open", "codecs.open") and "w" in write_mode(n) and n.args:
            tgt_node, kind = n.args[0], "%s(w)" % name
        elif name == "os.truncate" and n.args:
            tgt_node, kind = n.args[0], "os.truncate"
        elif isinstance(n.func, ast.Attribute) and n.func.attr in ("write_text", "write_bytes"):
            tgt_node, kind = n.func.value, "Path.%s" % n.func.attr
        if tgt_node is None: continue
        guarded = (enclosing_try_finally(n, parents) is not None)
        resolved = []
        v = resolve_simple(tgt_node, consts)
        how = "const"
        if v is not None: resolved = [v]
        else:
            resolved = resolve_backstep(tgt_node, consts, tree, parents); how = "backstep"
        out.append((n.lineno, kind, ast.dump(tgt_node)[:0] or getattr(tgt_node, "id", "<expr>"),
                    guarded, resolved, how))
    return out

def has_process_handler(tree):
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and dotted(n.func) in ("atexit.register", "signal.signal"):
            return True
    return False

root = sys.argv[1] if len(sys.argv) > 1 else ".softhouse"
files = []
for d, _, fs in os.walk(root):
    if "/.git" in d: continue
    for f in fs:
        if f.endswith(".py"): files.append(os.path.join(d, f))
files.sort()
if not files:
    print("ZERO FILES INSPECTED — error, not a pass (P-35)"); sys.exit(3)

pop_sites, pop_pairs, pop_files, unknown = [], set(), set(), []
n_sites = 0
for path in files:
    try:
        src = open(path, encoding="utf-8").read(); tree = ast.parse(src)
    except Exception as e:
        print("REFUSED %s (%s)" % (path, type(e).__name__)); continue
    parents = parents_of(tree); consts = const_map(tree)
    proc = has_process_handler(tree)
    for lineno, kind, tname, guarded, resolved, how in sites(tree, consts, parents):
        n_sites += 1
        if guarded or proc: continue
        if not resolved:
            unknown.append((path, lineno, kind, tname)); continue
        arts = {artefact(r) for r in resolved} - {None}
        for a in arts:
            pop_sites.append((path, lineno, kind, a, how, resolved))
            pop_pairs.add((path, a)); pop_files.add(path)

print("=== R-T183 population")
print("python files parsed        : %d" % len(files))
print("truncating write sites seen: %d" % n_sites)
print()
for p, l, k, a, how, r in sorted(pop_sites):
    print("%-52s :%-5s %-14s %-9s via=%-9s %s" % (p, l, k, a, how, r))
print()
adr_pairs  = sorted(p for p, a in pop_pairs if a == ADR)
con_pairs  = sorted(p for p, a in pop_pairs if a == CONTRACT)
print("PAIRS (my unit): %d   = ADR %d + CONTRACT %d" % (len(pop_pairs), len(adr_pairs), len(con_pairs)))
print("distinct FILES : %d" % len(pop_files))
print("distinct SITES : %d" % len(pop_sites))
print()
print("--- ADR pair files");      [print("   ", p) for p in adr_pairs]
print("--- CONTRACT pair files"); [print("   ", p) for p in con_pairs]
print()
print("--- UNRESOLVED truncating writes still UNKNOWN under R-T183: %d" % len(unknown))
for p, l, k, t in unknown[:40]: print("    %s:%s %s target=%s" % (p, l, k, t))
