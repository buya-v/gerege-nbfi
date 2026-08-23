#!/usr/bin/env python3
"""T304 census pass 2 — resolve each destructive operation's TARGET and ask git whether
that target contains COMMITTED (tracked) files.

Pass 1 (`10-census.py`) counted destructive OPERATIONS: 5313 of them. That number is not
the property. The property F-T283-6 names is:

    an instrument that destroys a path which CONTAINS COMMITTED EVIDENCE.

So this pass extracts the operand of each destructive call, expands what it can, and runs
`git ls-files -- <target>` to count the tracked files underneath it. Zero tracked files
underneath => the operation cannot destroy committed evidence, whatever else it does.

RESOLVER CAPABILITY (stated so the blind spots are on the record):
  * shell:  literal operands; `$VAR` / `${VAR}` where VAR has a literal `VAR=...`
            assignment earlier in the same file; `$(dirname "$0")`-rooted paths mapped to
            the script's own directory; `"$REPO"`/`"$ROOT"`-style repo roots mapped to the
            repo root when their assignment resolves there.
  * python: literal string operands; module-level `NAME = "literal"`; os.path.join of
            those; f-strings whose replacement fields are all resolvable.
  UNRESOLVED operands are NOT silently dropped -- they are reported in their own bucket and
  listed, because an unresolved target is an unknown, not a safe one.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))

DESTRUCTIVE = {"rm-rf", "rm-plain", "rmtree", "os-remove", "path-unlink",
               "mv", "shutil-move", "git-checkout-dd", "sed-i", "truncate"}
OVERWRITE = {"redirect", "py-write", "write-text", "tee"}

_tracked_cache = {}


def tracked_count(path):
    """How many TRACKED files live at or under `path` (repo-relative)?"""
    if path in _tracked_cache:
        return _tracked_cache[path]
    p = path.rstrip("/")
    if not p or p in (".", "/"):
        n = -1  # whole repo; flag rather than count
    else:
        r = subprocess.run(["git", "ls-files", "-z", "--", p], cwd=ROOT,
                           capture_output=True)
        n = len([x for x in r.stdout.decode("utf-8", "replace").split("\0") if x])
    _tracked_cache[path] = n
    return n


VAR_RX = re.compile(r"^\s*(?:export\s+|local\s+|readonly\s+|declare\s+-\w+\s+)?"
                    r"([A-Za-z_][A-Za-z0-9_]*)=(.+?)\s*$")


def shell_vars(relfile):
    """Literal VAR=... assignments in a shell file, best-effort."""
    env = {}
    path = os.path.join(ROOT, relfile)
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        return env
    scriptdir = os.path.dirname(relfile)
    for ln in lines:
        m = VAR_RX.match(ln)
        if not m:
            continue
        name, val = m.group(1), m.group(2)
        val = val.split("#", 1)[0].strip() if not val.startswith(("'", '"')) else val
        val = val.strip()
        if val.startswith(('"', "'")) and val.endswith(('"', "'")) and len(val) > 1:
            val = val[1:-1]
        # common repo-root idioms
        if re.search(r"cd\s+\"?\$\(dirname", val) or "git rev-parse --show-toplevel" in val:
            env[name] = ""            # repo root
            continue
        if re.fullmatch(r"\$\(\s*(cd\s+)?\"?\$\(dirname\s+\"?\$\{?BASH_SOURCE\[0\]\}?\"?\)\"?[^)]*\)", val):
            env[name] = scriptdir
            continue
        if "mktemp" in val or "$(mktemp" in val:
            env[name] = "\0MKTEMP"
            continue
        env[name] = val
    return env


def expand_shell(tok, env, relfile, depth=0):
    if depth > 6:
        return tok
    scriptdir = os.path.dirname(relfile)
    tok = tok.replace('$(dirname "$0")', scriptdir).replace("$(dirname $0)", scriptdir)
    tok = re.sub(r"\$\(\s*cd\s+\"?\$\(dirname[^)]*\)\"?[^)]*&&\s*pwd\s*\)", scriptdir, tok)

    def sub(m):
        name = m.group(1) or m.group(2)
        if name in env:
            return env[name]
        return "\0UNRES:%s" % name

    new = re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)", sub, tok)
    if new != tok:
        return expand_shell(new, env, relfile, depth + 1)
    return new


ARGSPLIT = re.compile(r"""'([^']*)'|"([^"]*)"|(\S+)""")


def shell_operands(text, verb):
    """Operands of `rm ...` / `mv ...` etc. on a logical shell line."""
    # take the segment starting at the verb, stop at a shell operator
    m = re.search(r"\b%s\b" % re.escape(verb), text)
    if not m:
        return []
    seg = text[m.end():]
    seg = re.split(r"(?:&&|\|\||[;|)]|\bthen\b|\bdo\b|\bfi\b)", seg)[0]
    ops = []
    for g in ARGSPLIT.finditer(seg):
        tok = g.group(1) or g.group(2) or g.group(3) or ""
        if not tok:
            continue
        if tok.startswith("-"):
            continue
        if tok.startswith(("2>", ">", "<")):
            continue
        ops.append(tok)
    return ops


PY_LIT = re.compile(r"""\(\s*(?:Path\s*\(\s*)?["']([^"']+)["']""")


def py_operand(text):
    m = PY_LIT.search(text)
    return m.group(1) if m else None


def normalise(p, relfile):
    """Repo-relative, or None if it is clearly outside the repo / unresolvable."""
    if not p or "\0" in p:
        return None
    if p.startswith(("/tmp", "/var/folders", "/dev/")):
        return "\0EXTERNAL"
    if "*" in p or "?" in p:
        # glob: keep, git ls-files understands pathspecs
        pass
    if os.path.isabs(p):
        real = os.path.normpath(p)
        if real.startswith(ROOT + "/"):
            return os.path.relpath(real, ROOT)
        return "\0EXTERNAL"
    q = os.path.normpath(os.path.join(os.path.dirname(relfile), p)) if p.startswith((".", "..")) else p
    if q.startswith(".."):
        return "\0EXTERNAL"
    return q


def main():
    hits = json.load(open(os.path.join(HERE, "evidence", "10-census-hits.json")))["hits"]
    envcache = {}
    rows = []
    for h in hits:
        fam = h["pattern"]
        if fam not in DESTRUCTIVE and fam not in OVERWRITE:
            continue
        rel, text = h["file"], h["text"]
        target_raw = None
        if fam in ("rm-rf", "rm-plain"):
            ops = shell_operands(text, "rm")
            target_raw = ops[0] if ops else None
        elif fam == "mv":
            ops = shell_operands(text, "mv")
            target_raw = ops[-1] if len(ops) >= 2 else None
        elif fam == "sed-i":
            ops = shell_operands(text, "sed")
            target_raw = ops[-1] if ops else None
        elif fam == "truncate":
            ops = shell_operands(text, "truncate")
            target_raw = ops[-1] if ops else None
        elif fam == "git-checkout-dd":
            m = re.search(r"git\s+checkout\s+--\s+(\S+)", text)
            target_raw = m.group(1) if m else None
        elif fam in ("rmtree", "os-remove", "path-unlink", "write-text", "py-write", "shutil-move"):
            target_raw = py_operand(text)
        elif fam == "redirect":
            m = re.search(r"(?<![0-9<>&|])>(?!>)\s*(\"[^\"]+\"|'[^']+'|\S+)", text)
            target_raw = m.group(1).strip("\"'") if m else None
        elif fam == "tee":
            ops = shell_operands(text, "tee")
            target_raw = ops[0] if ops else None

        if rel.endswith(".py"):
            expanded = target_raw
        else:
            if rel not in envcache:
                envcache[rel] = shell_vars(rel)
            expanded = expand_shell(target_raw, envcache[rel], rel) if target_raw else None

        norm = normalise(expanded, rel) if expanded else None
        if norm is None:
            status, n = "UNRESOLVED", None
        elif norm == "\0EXTERNAL" or (expanded and "\0MKTEMP" in expanded):
            status, n = "SCRATCH_OR_EXTERNAL", 0
        elif "\0UNRES" in norm:
            status, n = "UNRESOLVED", None
        else:
            n = tracked_count(norm)
            status = "TRACKED" if n and n > 0 else ("WHOLE_REPO" if n == -1 else "UNTRACKED")
        rows.append({**h, "target_raw": target_raw, "target": None if norm and "\0" in norm else norm,
                     "status": status, "tracked_files": n,
                     "family": "destructive" if fam in DESTRUCTIVE else "overwrite"})

    with open(os.path.join(HERE, "evidence", "20-resolved.json"), "w") as fh:
        json.dump(rows, fh, indent=1)

    def tally(fam):
        sub = [r for r in rows if r["family"] == fam]
        agg = {}
        for r in sub:
            agg[r["status"]] = agg.get(r["status"], 0) + 1
        return len(sub), agg

    for fam in ("destructive", "overwrite"):
        tot, agg = tally(fam)
        print("%s: %d operations" % (fam.upper(), tot))
        for k in sorted(agg):
            print("   %-20s %5d" % (k, agg[k]))
        print()

    print("=== DESTRUCTIVE operations whose target CONTAINS TRACKED FILES ===")
    tr = [r for r in rows if r["family"] == "destructive" and r["status"] in ("TRACKED", "WHOLE_REPO")]
    tr.sort(key=lambda r: (-(r["tracked_files"] or 0), r["file"], r["line"]))
    for r in tr:
        print("%-6s %5s  %s:%s  -> %s" % (r["pattern"], r["tracked_files"], r["file"], r["line"], r["target"]))
    print("TOTAL: %d" % len(tr))

    print()
    print("=== UNRESOLVED destructive operands (blind spot, listed not dropped) ===")
    un = [r for r in rows if r["family"] == "destructive" and r["status"] == "UNRESOLVED"]
    for r in un:
        print("%-6s %s:%s  raw=%r" % (r["pattern"], r["file"], r["line"], r["target_raw"]))
    print("TOTAL UNRESOLVED: %d" % len(un))


if __name__ == "__main__":
    sys.exit(main())
