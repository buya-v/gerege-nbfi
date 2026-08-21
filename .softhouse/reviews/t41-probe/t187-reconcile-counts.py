#!/usr/bin/env python3
"""T187: reconcile the FOUR counts of this population by re-deriving each one
under the rule it used.  The counts differ because the RULES differ; nothing
here averages them and nothing here picks one.

The four:
  driver  21 files "doing in-place truncating writes with a `docs/adr/DEC-1`
          path", plus 8 files "merely MENTIONING contract.go"
  T178    21 targeting the ratified DEC-1 + 4 targeting contract.go = 25
  T179    22 = 17 ADR + 5 contract.go, from a parser-based classifier
  T187    25 = 20 ADR + 7 contract.go, of which 2 write BOTH  (t187-census.py)

Every number below is measured from the PRE-FIX bytes at commit 16d5252 - the
commit T187 branched from - read with `git show`, never from the working tree,
so this stays re-derivable after the fix lands.  Read-only throughout.
"""
import ast
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
REV = "16d525213ea088984f11cba281419d59f039c0f9"
REL = ".softhouse/reviews/t41-probe"

ADR = "docs/adr/DEC-1-schedule-generator-adapter.md"
GO = "nexus/internal/apps/loanschedule/contract/contract.go"


def git(*a):
    r = subprocess.run(["git"] + list(a), cwd=REPO, capture_output=True)
    if r.returncode != 0:
        sys.exit("git %s failed" % " ".join(a))
    return r.stdout


def consts(tree):
    out = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) \
                and isinstance(n.value.value, str):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    out[t.id] = n.value.value
    return out


def direct_write_targets(tree):
    """Resolve ONLY literals and module-level string constants - deliberately
    NOT following a helper's `path` parameter back to its call sites."""
    c = consts(tree)
    out = set()
    for n in ast.walk(tree):
        f = getattr(n, "func", None)
        if not (isinstance(n, ast.Call) and f is not None):
            continue
        if getattr(f, "attr", getattr(f, "id", None)) != "open":
            continue
        if len(n.args) < 2:
            continue
        m = n.args[1]
        if not (isinstance(m, ast.Constant) and "w" in str(m.value)):
            continue
        a = n.args[0]
        if isinstance(a, ast.Constant):
            out.add(a.value)
        elif isinstance(a, ast.Name) and a.id in c:
            out.add(c[a.id])
        else:
            out.add(None)
    return out


names = [x for x in git("ls-tree", "--name-only", REV,
                        REL + "/").decode().split()
         if x.endswith(".py")]
rows = []
for path in sorted(names):
    n = os.path.basename(path)
    src = git("show", "%s:%s" % (REV, path)).decode("utf-8")
    tree = ast.parse(src)
    rows.append({"n": n, "src": src,
                 "m_adr": "docs/adr/DEC-1" in src,
                 "m_go": "contract.go" in src,
                 "trunc": any(True for x in ast.walk(tree)
                              if isinstance(x, ast.Call)
                              and getattr(x.func, "attr",
                                          getattr(x.func, "id", None)) == "open"
                              and len(x.args) >= 2
                              and isinstance(x.args[1], ast.Constant)
                              and "w" in str(x.args[1].value)),
                 "direct": direct_write_targets(tree)})


def show(title, sel):
    got = sorted(r["n"] for r in rows if sel(r))
    print("  %-58s %2d" % (title, len(got)))
    print("      %s" % ", ".join(got))
    return got


print("PRE-FIX bytes read from %s (%d .py files)\n" % (REV[:7], len(rows)))

print("R1  MENTIONS the DEC-1 path anywhere  -> reproduces the driver's 21 "
      "and T178's 21")
a1 = show("mentions docs/adr/DEC-1", lambda r: r["m_adr"])
print("R1b MENTIONS contract.go anywhere     -> reproduces the driver's 8")
show("mentions contract.go", lambda r: r["m_go"])

print("\nR2  MENTIONS the DEC-1 path AND has a truncating write-open")
a2 = show("mentions + truncating write", lambda r: r["m_adr"] and r["trunc"])
print("      DIFFERENCE R1 - R2 = %s"
      % ", ".join(sorted(set(a1) - set(a2))))
print("      That file is a READ-ONLY grep.  It is why 21 is a MENTION count "
      "and not\n      a writer count.")

print("\nR3  DIRECT truncating write, target from a literal or a module-level"
      "\n    constant only (no helper-parameter resolution) -> reproduces "
      "T179's 22 = 17 + 5")
show("R3 ADR", lambda r: ADR in r["direct"])
show("R3 contract.go", lambda r: GO in r["direct"])
show("R3 UNDETERMINED (write target is a helper parameter)",
     lambda r: None in r["direct"])

print("\nR4  files named edit_go*.py with a module-level nexus/... constant"
      "\n    -> reproduces T178's 4")
show("R4 contract.go", lambda r: r["n"].startswith("edit_go")
     and GO in r["direct"])

print("\nR5  T187's rule (t187-census.py): a truncating write whose target"
      "\n    resolves statically, INCLUDING through a helper's `path`"
      "\n    parameter back to its call sites.  Run t187-census.py"
      "\n    --scan=<a checkout of the pre-fix bytes> for the full table:"
      "\n    25 files = 20 DEC-1 + 7 contract.go, 2 of them writing BOTH.")
