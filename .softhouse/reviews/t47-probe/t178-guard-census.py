#!/usr/bin/env python3
"""T178 guard census - the successor to `t167-sibling-census.py`'s guard
columns, and the standing tripwire for this family of scripts.

WHY A SUCCESSOR EXISTS AT ALL, because this is the interesting part.
T167's census answers "is this file guarded?" from the file's OWN AST: it
counts `ast.Try` nodes and looks for an `os.replace` call in the same file.
T178 hardened the eight remaining rewriters by delegating the guard to a shared
module (`t178_guard.py`), for the P-27 reason that eight inline copies of one
guard is one guard and seven time bombs.  The consequence, which is P-48 and
P-49 arriving together: **T167's census reads the hardened files as
`try 0 / atomic False` - i.e. UNGUARDED - because the guard is no longer
textually in them.**  Nothing about T167's census was wrong when it was
written; T178's change moved what it was measuring, and that movement is
invisible in T178's own diff.  Run against the eight files today it also mis-
labels `t47_edit_7.py`'s target as the ADR, because it reads a `DOC`/`GO`
constant that the hardened files no longer define.

So this census answers the same three questions, resolving delegation:

  1. IS THE WRITE GUARDED?  Either the file writes atomically itself
     (`os.replace`, T167's shape for `t47_edit_1.py`), or it delegates every
     write to `t178_guard.commit` and never opens its target for writing.
     A file that does neither and calls `open(..., "w")` / `write_text` on a
     path it hard-wires is UNGUARDED.
  2. WHAT DOES IT WRITE?  Resolved from the hard-wired `DOC`/`GO` constant
     (pre-fix shape) or from the `guard.RATIFIED_ADR` / `guard.FROZEN_CONTRACT`
     policy argument (post-fix shape).
  3. COULD IT REACH THE LIVE ARTEFACT?  Two independent answers, and both are
     reported because they fail in different directions:
       (a) ANCHORS - are all the string anchors it must find still present
           exactly once in the live artefact?  This is T167's question.
       (b) CONTENT GATE - does the live artefact's sha256 equal the file's
           pinned `BEFORE_SHA256`?  A guarded file with a content gate cannot
           reach the artefact even if every anchor is live, and this is the
           check that stays true as the document is revised: it fires if a
           future revision ever lands back on a pinned pre-edit blob.
     Answer (a) is a statement about TODAY'S TEXT and is not a guarantee about
     tomorrow's.  Answer (b) is a statement about the guard.

NOTHING HERE IS EXECUTED.  Every question is answered from the AST and from
string membership in the target files.  Running one of these scripts to find
out what it does is the defect, not the test.

P-40: this census COUNTS WHAT IT SKIPPED.  There is no bare `except: continue`
anywhere in it; a file it cannot parse is NAMED and counted, never dropped, and
an anchor it cannot resolve statically is reported as UNDETERMINED.

Exit 0 = no file in the family can reach a ratified/frozen artefact.
Exit 1 = at least one can, or at least one file could not be measured.
"""
import ast
import glob
import io
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
HERE = os.path.dirname(os.path.abspath(__file__))
ADR_REL = "docs/adr/DEC-1-schedule-generator-adapter.md"
GO_REL = "nexus/internal/apps/loanschedule/contract/contract.go"

# Optional argument: a directory holding an alternative copy of the family, so
# this census can be driven RED against the PRE-FIX bytes.  It never changes
# which LIVE artefacts are read - those are always the real ones.
SCAN = HERE
ARGS = sys.argv[1:]
for a in ARGS:
    if a.startswith("--scan="):
        SCAN = a.split("=", 1)[1]
    else:
        sys.stderr.write("usage: t178-guard-census.py [--scan=DIR]\n")
        sys.exit(1)


def sha256_text(t):
    import hashlib
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def const_str(tree, name):
    """The module-level string value assigned to `name`, or None."""
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 \
                and getattr(n.targets[0], "id", "") == name:
            if isinstance(n.value, ast.Constant) \
                    and isinstance(n.value.value, str):
                return n.value.value
    return None


def const_expr(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for tgt in n.targets:
                if getattr(tgt, "id", "") == name:
                    return ast.unparse(n.value)
    return None


def guard_policy(tree):
    """`RATIFIED_ADR` / `FROZEN_CONTRACT` if the file delegates to the shared
    guard, else None."""
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr == "load" \
                and getattr(n.func.value, "id", "") == "guard":
            for a in list(n.args) + [k.value for k in n.keywords]:
                if isinstance(a, ast.Attribute) \
                        and getattr(a.value, "id", "") == "guard":
                    return a.attr
    return None


def delegates_commit(tree):
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr == "commit" \
                and getattr(n.func.value, "id", "") == "guard":
            return True
    return False


def raw_write_sites(tree):
    """Calls that open a path for writing, or write text to a path, directly.
    `os.fdopen` is excluded: it takes a file DESCRIPTOR from mkstemp, not a
    path, and is the atomic path."""
    out = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        nm = None
        if isinstance(f, ast.Name):
            nm = f.id
        elif isinstance(f, ast.Attribute):
            nm = f.attr
        if nm in ("open",) and len(n.args) > 1:
            m = n.args[1]
            if isinstance(m, ast.Constant) and isinstance(m.value, str) \
                    and ("w" in m.value or "a" in m.value):
                out.append(n.lineno)
        if nm in ("write_text", "write_bytes"):
            out.append(n.lineno)
    return out


def has_os_replace(tree):
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr == "replace" \
                and getattr(n.func.value, "id", "") == "os":
            return True
    return False


def anchors_of(tree):
    env = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 \
                and isinstance(n.targets[0], ast.Name):
            if isinstance(n.value, ast.Constant) \
                    and isinstance(n.value.value, str):
                env[n.targets[0].id] = n.value.value
            elif isinstance(n.value, ast.JoinedStr):
                continue

    def resolve(a):
        if isinstance(a, ast.Name):
            return env.get(a.id)
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            return a.value
        if isinstance(a, ast.BinOp) or isinstance(a, ast.Tuple):
            return None
        return None

    nodes = []
    for top in tree.body:
        if isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef,
                            ast.ClassDef)):
            continue
        nodes.extend(ast.walk(top))
    out, undet = [], 0
    for n in nodes:
        if not isinstance(n, ast.Call) or not n.args:
            continue
        f = n.func
        gate = False
        if isinstance(f, ast.Name) and f.id in ("rep", "sub", "replace_one"):
            gate = True
        if isinstance(f, ast.Attribute) and f.attr in ("count",):
            gate = True
        if isinstance(f, ast.Attribute) and f.attr == "rep" \
                and getattr(f.value, "id", "") == "guard":
            gate = True
        if not gate:
            continue
        # guard.rep(s, old, new): the anchor is argument 2.
        idx = 1 if (isinstance(f, ast.Attribute) and f.attr == "rep") else 0
        if len(n.args) <= idx:
            undet += 1
            continue
        v = resolve(n.args[idx])
        if isinstance(v, str) and len(v) > 40:
            out.append((n.lineno, v))
        else:
            undet += 1
    seen, uniq = set(), []
    for ln, v in out:
        if v not in seen:
            seen.add(v)
            uniq.append((ln, v))
    return uniq, undet


adr = io.open(os.path.join(REPO, ADR_REL), encoding="utf-8").read()
go = io.open(os.path.join(REPO, GO_REL), encoding="utf-8").read()
adr_sha, go_sha = sha256_text(adr), sha256_text(go)

print("T178 guard census   (scanning %s)" % SCAN)
print("live target 1: %s  sha256 %s" % (ADR_REL, adr_sha))
print("live target 2: %s  sha256 %s" % (GO_REL, go_sha))
print("\nBoth are hard `user` gates to amend: CLAUDE.md, \"Any change to a "
      "ratified DEC-n\nor the frozen adapter contract\".  contract.go "
      "additionally carries gate G-3.\n")
print("%-16s %-9s %-11s %-13s %-9s %-6s %s"
      % ("file", "guard", "writes", "target", "anchors", "live", "content gate"))
print("-" * 104)

reachable, unmeasured, skipped = [], [], []
files = sorted(glob.glob(os.path.join(SCAN, "t47_edit_*.py")))
for p in files:
    base = os.path.basename(p)
    try:
        src = io.open(p, encoding="utf-8").read()
        tree = ast.parse(src)
    except (IOError, OSError, SyntaxError, UnicodeDecodeError) as e:
        unmeasured.append("%s: %s" % (base, e))
        print("%-16s %s" % (base, "COULD NOT PARSE - COUNTED, NOT DROPPED"))
        continue

    pol = guard_policy(tree)
    doc, goc = const_expr(tree, "DOC"), const_expr(tree, "GO")
    if pol == "FROZEN_CONTRACT" or (goc and not doc):
        target, tgt_sha, tname = go, go_sha, "contract.go"
    else:
        target, tgt_sha, tname = adr, adr_sha, "DEC-1 ADR"

    raw = raw_write_sites(tree)
    if has_os_replace(tree) and not raw:
        gu, how = "GUARDED", "os.replace"
    elif delegates_commit(tree) and pol and not raw:
        gu, how = "GUARDED", "guard.commit"
    else:
        gu, how = "UNGUARDED", "open(...,'w')" if raw else "none"

    anc, undet = anchors_of(tree)
    live = [ln for ln, a in anc if target.count(a) == 1]
    before = const_str(tree, "BEFORE_SHA256")
    if before is None:
        cg = "NONE - any content"
        gate_blocks = False
    elif before == tgt_sha:
        cg = "OPEN - matches live!"
        gate_blocks = False
    else:
        cg = "closed (%s...)" % before[:8]
        gate_blocks = True

    note = ""
    if gu == "UNGUARDED" and anc and len(live) == len(anc) and not undet:
        note = "   <<< ALL ANCHORS LIVE - would rewrite the target TODAY"
        reachable.append(base)
    elif gu == "UNGUARDED" and not gate_blocks:
        note = "   (unguarded; inert only because %d/%d anchors are gone)" \
            % (len(anc) - len(live), len(anc))
        skipped.append(base)
    if undet:
        note += "   (%d anchor(s) UNDETERMINED)" % undet

    print("%-16s %-9s %-11s %-13s %-9d %-6d %s%s"
          % (base, gu, how, tname, len(anc), len(live), cg, note))

print("""
Reading:
  guard        GUARDED = every write is atomic (os.replace) or delegated to
               t178_guard.commit, and the file opens no path for writing.
  anchors      string anchors the script must find before it writes.
  live         how many are still present EXACTLY ONCE in the LIVE artefact.
               This is a fact about today's document, never a guarantee.
  content gate `closed` = the file pins a BEFORE_SHA256 that is NOT the live
               artefact's, so it cannot reach it whatever the anchors say.
               `NONE` = it will edit whatever it finds.""")

print("\nfiles measured        %d" % len(files))
print("files UNMEASURED      %d%s"
      % (len(unmeasured), (" - " + "; ".join(unmeasured)) if unmeasured else ""))
print("unguarded + all anchors live (LIVE BYPASS)   %d%s"
      % (len(reachable), (" - " + ", ".join(reachable)) if reachable else ""))
print("unguarded + no content gate, inert TODAY ONLY %d%s"
      % (len(skipped), (" - " + ", ".join(skipped)) if skipped else ""))

sys.exit(1 if (reachable or unmeasured or skipped) else 0)
