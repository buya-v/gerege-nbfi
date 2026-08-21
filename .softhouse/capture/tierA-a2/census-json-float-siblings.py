#!/usr/bin/env python3
"""T163 — P-26 sibling census: sweep the tierA-a2 capture rig for the CONCEPT that made
resolve7.py a defect, not for the sentence that described it.

The concept is not "the string `parse_float` is missing".  It is:

    A NUMBER FROM A MONEY DOCUMENT IS CONVERTED TO A BINARY DOUBLE.

which happens by four routes, and this sweep looks for all four:

  R1  `json.load` / `json.loads` with no `parse_float=`            (read side)
  R2  `json.dump` / `json.dumps` of a document parsed that way     (write side — the one
      that made resolve7.py corrupt the WIRE rather than merely the analysis)
  R3  a bare `float(...)` call on anything                          (explicit conversion)
  R4  `json.load` inside a `python3 -c` in a SHELL script           (invisible to any
      Python-file sweep; run-220-a2-7-runtime.sh:34 is exactly this shape)

DETECTED WITH A PARSER, NOT A REGEX (P-48 rule 1).  `analyze7.py`'s own float guard greps
whole-file source for `parse_float` and MATCHES IT IN ITS OWN DOCSTRING, so deleting the
call leaves the guard green — A2-11 measured that, and it is open as T164.  This sweep
therefore walks the AST, so a call site cannot be confused with a comment, a docstring, or
a string literal being written into another document.  R4 alone cannot be done with an
AST over the .py files, because the code is inside a shell string; those hits are found
textually, the embedded snippet is then PARSED, and the limitation is stated below.

RANKING.  A hit is graded by what its output reaches, because that is what P-25 says the
test is — "if this number is wrong, does a wrong money claim reach a human?":

  WIRE      the script writes a REQUEST BODY that is POSTed to the reference oracle.
            This is the resolve7.py class.  Worst: it corrupts the OBSERVATION.
  ANALYSIS  the script reads captures and produces numbers a human reads.  This is the
            T145 class.
  INERT     the script handles no document that can carry a number.

GUARD SHAPE (P-35): counts are positive and printed; ZERO FILES SWEPT IS AN ERROR.  Every
file is placed in exactly one bucket and every bucket is printed in full.
"""
import ast
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
FAILS = []

# Which scripts write a body that is POSTed.  Derived from the run-*.sh recipes, not
# guessed: a script is WIRE if a run-*.sh feeds its output to cap.sh/cap8.sh as a body.
WIRE_WRITERS = set()


def check(label, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + label + (("\n          " + detail) if detail else ""))
    if not cond:
        FAILS.append(label)


def is_json_call(node, names):
    """(module, attr) if `node` is a call to json.<attr>, else None."""
    f = node.func
    if isinstance(f, ast.Attribute) and f.attr in names:
        if isinstance(f.value, ast.Name) and f.value.id == "json":
            return f.attr
    if isinstance(f, ast.Name) and f.id in names:
        return f.id
    return None


def scan_source(src, label):
    """Every R1/R2/R3 hit in `src`.  Returns list of (route, line, detail)."""
    hits = []
    tree = ast.parse(src, filename=label)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        kw = {k.arg for k in node.keywords if k.arg}
        a = is_json_call(node, {"load", "loads"})
        if a:
            if "parse_float" not in kw:
                hits.append(("R1", node.lineno, "json.%s(...) with no parse_float=" % a))
        b = is_json_call(node, {"dump", "dumps"})
        if b:
            hits.append(("R2", node.lineno, "json.%s(...) re-serialises" % b))
        if isinstance(node.func, ast.Name) and node.func.id == "float":
            hits.append(("R3", node.lineno, "float(...) constructed explicitly"))
    return hits


# ------------------------------------------------------------------ which are WIRE
# GETTING THIS SET WRONG IS HOW A SWEEP LIES, AND I GOT IT WRONG TWICE BEFORE THIS.
#   attempt 1: derived WIRE from the run-*.sh recipes only  -> {resolve7.py}, silently
#              missing all seven mkreq*.py, which write request bodies and are invoked by
#              hand rather than by a recipe.  UNDER-reported the risk.
#   attempt 2: "any file naming a req/ path"  -> 17 files, including manifest.py (which
#              only HASHES req/) and five provers (which write req/ inside a
#              tempfile.mkdtemp sandbox, never into the committed tree).  OVER-reported,
#              which is just as bad: it buries the two files that matter.
# So: CANDIDATES are generated mechanically, CLASSIFICATION is declared and hand-read, and
# THE SWEEP FAILS ON ANY CANDIDATE THAT IS NOT CLASSIFIED.  That is P-48 rule 3 — report
# the population, then hand-read the exceptions — with the allowlist made unable to hide a
# new arrival.
pyfiles = sorted(f for f in os.listdir(DIR) if f.endswith(".py"))
shfiles = sorted(f for f in os.listdir(DIR) if f.endswith(".sh"))

CANDIDATE_ROUTE = {}
for f in pyfiles:
    try:
        tree = ast.parse(open(os.path.join(DIR, f)).read(), filename=f)
    except SyntaxError:
        continue
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            v = n.value
            if v == "req" or v.startswith("req/") or v.endswith("/req"):
                CANDIDATE_ROUTE.setdefault(f, set()).add("names a req/ path (%r)" % v)
                break
for sh in shfiles:
    text = open(os.path.join(DIR, sh)).read()
    for m in re.finditer(r'python3\s+"?\$?\{?DIR\}?/?([A-Za-z0-9_.\-]+\.py)', text):
        if m.group(1) in pyfiles:
            CANDIDATE_ROUTE.setdefault(m.group(1), set()).add("invoked by %s" % sh)

# Declared, hand-read.  Each verdict states WHY, and each was checked by reading the file.
CLASSIFICATION = {
    # --- WIRE: writes a request body into the COMMITTED req/ tree, which cap.sh POSTs.
    "mkreq.py":   ("WIRE", "generates committed req/*.json bodies; that is its purpose"),
    "mkreq2.py":  ("WIRE", "generates committed req/*.json bodies"),
    "mkreq3.py":  ("WIRE", "generates committed req/*.json bodies"),
    "mkreq4.py":  ("WIRE", "generates committed req/*.json bodies"),
    "mkreq5.py":  ("WIRE", "generates committed req/*.json bodies"),
    "mkreq6.py":  ("WIRE", "generates committed req/*.json bodies"),
    "mkreq7.py":  ("WIRE", "generates committed req/*.json bodies (A2-7's leg)"),
    "resolve7.py": ("WIRE", "wrote committed req/a2-7-loan-220-resolved.json; FROZEN, superseded"),
    "resolve8.py": ("WIRE", "T163's replacement resolver"),
    # --- NOT WIRE: reads req/, or writes req/ only inside a temp sandbox.
    "manifest.py": ("READS", "hashes req/; writes only MANIFEST.sha256"),
    "audit-req-float-roundtrip.py": ("READS", "reads req/ and out/; writes nothing"),
    "census-json-float-siblings.py": ("READS", "reads source; writes nothing"),
    "show.py":    ("READS", "prints a capture"),
    "analyze7.py": ("READS", "analyses captures — T145/T164 class, not this task's"),
    "rename1.py": ("READS", "renames capture files"),
    "prove-a2-7-additive.py":     ("SANDBOX", "tempfile.mkdtemp; never the committed tree"),
    "prove-cap-transport-red.py": ("SANDBOX", "tempfile.mkdtemp (line 92); req/ is the sandbox's"),
    "prove-cap8-wire-bytes.py":   ("SANDBOX", "tempfile.mkdtemp; local server, not the oracle"),
    "prove-manifest-red.py":      ("SANDBOX", "tempfile; manifest comparison only"),
    "prove-manifest-blind-red.py": ("SANDBOX", "tempfile.mkdtemp"),
    "prove-mkreq7-guard-red.py":  ("SANDBOX", "tempfile.mkdtemp (line 36); req/ is the sandbox's"),
    "prove-resolve8-float-red.py": ("SANDBOX", "tempfile.mkdtemp; runs COPIES of the resolvers"),
}
WIRE_ROUTE = {f: r for f, r in CANDIDATE_ROUTE.items()
              if CLASSIFICATION.get(f, ("?",))[0] == "WIRE"}
WIRE_WRITERS = {f for f in pyfiles if CLASSIFICATION.get(f, ("?",))[0] == "WIRE"}
UNCLASSIFIED = sorted(set(CANDIDATE_ROUTE) - set(CLASSIFICATION))

print("=" * 78)
print("T163 — P-26 sibling census over .softhouse/capture/tierA-a2/")
print("=" * 78)
print()
print("POPULATION: %d Python file(s), %d shell file(s)" % (len(pyfiles), len(shfiles)))
print()
print("CANDIDATES (mechanical) -> CLASSIFICATION (declared, hand-read).  %d candidate(s)."
      % len(CANDIDATE_ROUTE))
print("  %-32s %-8s %s" % ("file", "verdict", "why it is / is not a request-body writer"))
for f in sorted(CANDIDATE_ROUTE):
    verdict, why = CLASSIFICATION.get(f, ("!UNCLASS", "NOT IN THE DECLARED TABLE"))
    print("  %-32s %-8s %s" % (f, verdict, why))
print()
print("WIRE WRITERS (%d): %s" % (len(WIRE_WRITERS), sorted(WIRE_WRITERS)))
print()

rows, unparsed = [], []
for f in pyfiles:
    src = open(os.path.join(DIR, f)).read()
    try:
        hits = scan_source(src, f)
    except SyntaxError as e:
        unparsed.append((f, str(e)))
        continue
    tier = "WIRE" if f in WIRE_WRITERS else ("ANALYSIS" if hits else "INERT")
    rows.append((f, tier, hits))

print("R1/R2/R3 — Python, by AST")
print("  %-34s %-9s %-6s %s" % ("file", "reaches", "hits", "routes"))
for f, tier, hits in rows:
    routes = ",".join(sorted({h[0] for h in hits})) or "-"
    print("  %-34s %-9s %-6d %s" % (f, tier, len(hits), routes))
print()

flagged = [(f, tier, hits) for f, tier, hits in rows if hits]
print("DETAIL — every hit, printed in full, not sampled")
if not flagged:
    print("  (none)")
for f, tier, hits in flagged:
    print("  %s   [%s]" % (f, tier))
    for route, line, detail in hits:
        print("      %s  line %-4d %s" % (route, line, detail))
print()

# ------------------------------------------------------------------ R4: shell-embedded
print("R4 — json.load inside a `python3 -c` in a SHELL script (invisible to any .py sweep)")
r4 = []
for f in shfiles:
    text = open(os.path.join(DIR, f)).read()
    for m in re.finditer(r"python3\s+-c\s+'([^']*)'", text):
        snippet = m.group(1)
        line = text[:m.start()].count("\n") + 1
        try:
            hits = scan_source(snippet, "%s:%d" % (f, line))
        except SyntaxError as e:
            r4.append((f, line, snippet, "UNPARSEABLE: %s" % e))
            continue
        if any(h[0] == "R1" for h in hits):
            r4.append((f, line, snippet, "json.load with no parse_float"))
if not r4:
    print("  (none)")
for f, line, snippet, why in r4:
    print("  %s:%d  %s" % (f, line, why))
    print("      %s" % snippet)
print()
print("  LIMIT OF THIS ROUTE, STATED (P-26): this finds `python3 -c '...'` in SINGLE")
print("  quotes only.  A double-quoted -c, a heredoc, a `python3 - <<EOF`, or a snippet")
print("  built by string concatenation would not be found.  I grepped for those forms by")
print("  hand across the %d shell files and found none, but that hand-check is a claim" % len(shfiles))
print("  about this rig on this date, not a property the sweep enforces.")
print()

# ------------------------------------------------------------------ assertions
check("SWEEP IS NON-EMPTY — zero files swept would be an ERROR, not a pass",
      len(pyfiles) > 0 and len(shfiles) > 0,
      "%d .py, %d .sh" % (len(pyfiles), len(shfiles)))
check("EVERY PYTHON FILE WAS PARSED — an unparsed file is a hole, not a clean result",
      not unparsed, "unparsed: %r" % unparsed)
check("EVERY PYTHON FILE IS IN EXACTLY ONE BUCKET",
      len(rows) == len(pyfiles), "%d rows for %d files" % (len(rows), len(pyfiles)))
check("EVERY MECHANICAL CANDIDATE IS CLASSIFIED — a new script that touches req/ CANNOT "
      "slip through unread, which is what turns a hand-read table from an allowlist into "
      "a checkpoint (P-48 rule 3)",
      not UNCLASSIFIED, "unclassified: %r" % UNCLASSIFIED)

# ---------------------------------------------------- R5: a float LITERAL in a WIRE writer
print("R5 — a float LITERAL in a script that writes a request body")
print("  mkreq*.py build their bodies from Python literals and `json.dump` them.  They")
print("  have no json.load at all, so R1 cannot reach them — but `json.dumps(1200000.00)`")
print("  emits `1200000.0` just the same.  Their safety today rests entirely on every")
print("  literal in them being an int or a string, which nothing was checking.")
r5 = []
for f in pyfiles:
    tree = ast.parse(open(os.path.join(DIR, f)).read(), filename=f)
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and type(n.value) is float:
            r5.append((f, n.lineno, repr(n.value)))
if not r5:
    print("  none — 0 float literals across all %d Python files (measured, by AST)" % len(pyfiles))
for f, line, v in r5:
    print("  %s:%d  %s" % (f, line, v))
print()

# ---------------------------------------------------------------- terminal assertions
# resolve7.py and cap.sh produced committed evidence and are NOT edited (T114's standing
# ruling), so they stay flagged forever.  A guard that can only ever be red is as useless
# as one that can only ever be green, so the assertion is a REDIRECT, not an allowlist:
# a flagged WIRE writer passes only if SUPERSEDED.txt names a replacement AND THAT
# REPLACEMENT IS ITSELF VERIFIED CLEAN BY THIS SAME SWEEP.  Naming a replacement that does
# not exist, or that is dirty, fails.
supers, sup_missing = {}, []
sp = os.path.join(DIR, "SUPERSEDED.txt")
if os.path.exists(sp):
    for ln in open(sp):
        ln = ln.split("#")[0].strip()
        if not ln:
            continue
        parts = [x.strip() for x in ln.split("->")]
        if len(parts) == 2:
            supers[parts[0]] = parts[1]

hits_by_file = {f: hits for f, _t, hits in rows}
wire_flagged = [f for f, tier, hits in rows
                if tier == "WIRE" and any(h[0] == "R1" for h in hits)]
unredirected, bad_redirect = [], []
def redirect_state(replacement):
    """(ok, description) for a named replacement."""
    if not os.path.exists(os.path.join(DIR, replacement)):
        return False, "MISSING ON DISK"
    if replacement in hits_by_file:
        dirty = [h for h in hits_by_file[replacement] if h[0] == "R1"]
        return (not dirty), ("CLEAN (AST-verified, 0 R1)" if not dirty
                             else "ITSELF FLAGGED R1 at %s"
                             % ",".join(str(h[1]) for h in dirty))
    return True, "exists (shell — checked by prove-cap8-wire-bytes.py, not by this AST sweep)"


for f in wire_flagged:
    r = supers.get(f)
    if not r:
        unredirected.append(f)
        continue
    ok, why = redirect_state(r)
    if not ok:
        bad_redirect.append("%s -> %s (%s)" % (f, r, why))

print("SUPERSESSION REGISTER (SUPERSEDED.txt) — %d entr(ies)" % len(supers))
for k in sorted(supers):
    ok, why = redirect_state(supers[k])
    print("  %-30s -> %-32s %s" % (k, supers[k], why))
    if not ok and k not in wire_flagged:
        bad_redirect.append("%s -> %s (%s)" % (k, supers[k], why))
print()
check("EVERY WIRE WRITER IS EITHER CLEAN OR REDIRECTED to a named replacement — no "
      "request-body writer is left reading JSON through a binary double with nowhere to go",
      not unredirected,
      "flagged with no replacement: %r" % unredirected)
check("EVERY REDIRECT POINTS AT A REPLACEMENT THAT EXISTS AND IS ITSELF CLEAN — this is "
      "a redirect, not an allowlist: naming a dirty or missing replacement FAILS",
      not bad_redirect,
      "; ".join(bad_redirect) or "%d redirect(s) verified" % len(supers))
# The R5 set is WIRE *plus* anything still unclassified.  Found by sabotage: dropping in
# an unclassified `mkreq9.py` carrying `1200000.00` left R5 printing "0 float literals in
# WIRE writers" — true, and useless, because the offending file was not in WIRE yet.  Two
# guards that each rely on the other having run first is the P-36 shape.
r5_scope = WIRE_WRITERS | set(UNCLASSIFIED)
check("NO REQUEST-BODY WRITER CONTAINS A FLOAT LITERAL (R5) — scope is WIRE plus every "
      "UNCLASSIFIED candidate, so a new script cannot be invisible to this guard merely "
      "by not having been classified yet",
      not [x for x in r5 if x[0] in r5_scope],
      "%d float literal(s) across %d file(s) in scope: %s"
      % (len([x for x in r5 if x[0] in r5_scope]), len(r5_scope),
         [(f, l, v) for f, l, v in r5 if f in r5_scope] or "none"))

print()
print("OUT OF SCOPE HERE, STATED SO THE SWEEP IS NOT READ AS EXHAUSTIVE (P-26):")
print("  * The ANALYSIS-tier R1 hits below are the T145 class (74 .py files across")
print("    .softhouse/ read money through a binary double).  T145 is a separate OPEN task")
print("    and this sweep neither fixes nor grades them:")
for f, tier, hits in rows:
    if tier != "WIRE" and any(h[0] == "R1" for h in hits):
        print("      %-34s R1 at line(s) %s"
              % (f, ",".join(str(h[1]) for h in hits if h[0] == "R1")))
print("  * analyze7.py's float guard passes on its own DOCSTRING (P-48) — open as T164,")
print("    which depends on this task.  Not touched here.")
print("  * The R4 shell hits above extract an id into a URL, not money into a body.  They")
print("    are still the same shape and are carried as follow-ups, not fixed here.")
print("  * This sweep covers .softhouse/capture/tierA-a2/ ONLY, which is T163's files_hint.")

print()
print("FAILURES: %d" % len(FAILS))
for f in FAILS:
    print("  - " + f)
sys.exit(1 if FAILS else 0)
