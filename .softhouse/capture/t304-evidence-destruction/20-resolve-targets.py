#!/usr/bin/env python3
"""T304 census pass 2 — resolve each destructive operation's TARGET ROOT and ask git
whether that target contains COMMITTED (tracked) files.

Pass 1 (`10-census.py`) counted destructive OPERATIONS: 5313 of them over 1146 tracked
scripts. That number is NOT the property. The property F-T283-6 names is:

    an instrument that destroys a path which CONTAINS COMMITTED EVIDENCE.

The whole discrimination is in the ROOT of the operand. `rm -rf "$TMP/.softhouse/vectors"`
and `rm -rf "$REPO/.softhouse/vectors"` are textually near-identical and are opposite
verdicts: the first deletes a scratch clone, the second destroys the vector store.

So this pass classifies every shell variable in every script as one of

    SCRATCH   -- derived from mktemp / $TMPDIR / a /tmp path, directly or transitively
    REPO      -- the repository root (git rev-parse --show-toplevel, or a
                 $(cd "$(dirname "$0")"/.. && pwd) chain that lands on the root)
    SELFDIR   -- the script's own directory (or a descendant of it)
    LITERAL   -- a literal string
    UNKNOWN   -- everything else; NOT treated as safe, reported in its own bucket

and then resolves each destructive operand against that classification. A REPO- or
SELFDIR- or LITERAL-rooted operand is passed to `git ls-files -- <path>`; a non-zero count
means the operation destroys committed evidence.

`cd` INTO SCRATCH IS TRACKED TOO: a script that does `cd "$SCRATCH"` and then uses a
relative path is operating on the clone, not the repo. Scripts containing such a `cd` are
flagged so a relative operand in them is not mis-read as repo-relative.

BLIND SPOTS, stated rather than hidden:
  * operands built inside a loop from an array/glob the resolver cannot enumerate;
  * operands passed in as "$1" from a caller;
  * python operands built by a function parameter.
  These land in UNKNOWN and are listed individually at the end. UNKNOWN is not "clean".
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

_tc = {}


def tracked_count(path):
    if path in _tc:
        return _tc[path]
    p = path.rstrip("/")
    if not p or p in (".", "/"):
        n = -1
    else:
        r = subprocess.run(["git", "ls-files", "-z", "--", p], cwd=ROOT, capture_output=True)
        n = len([x for x in r.stdout.decode("utf-8", "replace").split("\0") if x])
    _tc[path] = n
    return n


SCRATCH_RX = re.compile(r"mktemp|TMPDIR|/tmp/|/var/folders|\$\(mktemp")
REPO_RX = re.compile(r"git\s+rev-parse\s+--show-toplevel")
SELF_RX = re.compile(r"dirname\s+[\"']?\$\{?(0|BASH_SOURCE\[0\])\}?")
# VAR=$(cd "$OTHER/../.." && pwd)   -- the root-walk idiom used across this repo
CDCHAIN_RX = re.compile(r"\$\(\s*cd\s+[\"']?\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?([^\"'&)]*)[\"']?\s*(?:&&|;)\s*pwd\s*\)")


def trailing_suffix(val):
    """Literal path fragment appended AFTER the last `$(...)` in an assignment RHS.

    `D="$(cd "$(dirname "$0")" && pwd)/ignoretest"` targets .../ignoretest, NOT the
    script's own directory. Dropping this suffix made the first draft of this resolver
    report `.softhouse/capture/t131-grep` (28 tracked files) as a destruction target when
    the real target is `.softhouse/capture/t131-grep/ignoretest` (0 tracked files) --
    a FALSE POSITIVE, and exactly the kind the brief warns is worse than no census.
    """
    v = val.strip().strip('"\'')
    depth = 0
    last = -1
    i = 0
    while i < len(v):
        if v.startswith("$(", i):
            depth += 1
            i += 2
            continue
        if v[i] == ")" and depth:
            depth -= 1
            if depth == 0:
                last = i
        i += 1
    if last < 0:
        return ""
    tail = v[last + 1:].strip('"\'')
    return tail.strip("/") if "$" not in tail else ""

ASSIGN_RX = re.compile(
    r"^\s*(?:export\s+|local\s+|readonly\s+|declare\s+(?:-\w+\s+)?)?"
    r"([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def classify_vars(relfile, text_lines):
    """name -> (kind, literal_or_None). Iterated to a fixpoint so transitive scratch propagates."""
    raw = {}
    order = []
    for ln in text_lines:
        if ln.lstrip().startswith("#"):
            continue
        m = ASSIGN_RX.match(ln)
        if not m:
            continue
        name, val = m.group(1), m.group(2).strip()
        raw[name] = val
        order.append(name)
    kinds = {}
    for _ in range(6):
        changed = False
        for name in order:
            val = raw[name]
            new = None
            if SCRATCH_RX.search(val):
                new = ("SCRATCH", None)
            elif REPO_RX.search(val):
                new = ("REPO", "")
            elif SELF_RX.search(val):
                # $(cd "$(dirname "$0")" && pwd)[/suffix]  -- with optional /.. walk-ups
                ups = val.count("/..")
                d = os.path.dirname(relfile)
                for _u in range(ups):
                    d = os.path.dirname(d)
                new = ("SELFDIR", os.path.normpath(os.path.join(d, trailing_suffix(val))))
            elif CDCHAIN_RX.search(val):
                # VAR=$(cd "$OTHER/rel" && pwd)  -- the dominant root-walk idiom here
                m2 = CDCHAIN_RX.search(val)
                base_name, rel_part = m2.group(1), (m2.group(2) or "")
                bk, bl = kinds.get(base_name, ("UNKNOWN", None))
                if bk == "SCRATCH":
                    new = ("SCRATCH", None)
                elif bk in ("REPO", "SELFDIR", "LITERAL") and bl is not None:
                    tail = os.path.join(rel_part.strip("/"), trailing_suffix(val)).strip("/")
                    p = os.path.normpath(os.path.join(bl, tail)) if tail else bl
                    if p in (".", "/", ""):
                        new = ("REPO", "")
                    elif p.startswith(".."):
                        new = ("UNKNOWN", None)
                    else:
                        new = ("SELFDIR", p)
                else:
                    new = ("UNKNOWN", None)
            else:
                refs = re.findall(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)", val)
                refs = [a or b for a, b in refs]
                if refs:
                    kk = [kinds.get(r, ("UNKNOWN", None)) for r in refs]
                    if any(k[0] == "SCRATCH" for k in kk):
                        new = ("SCRATCH", None)
                    elif all(k[0] in ("REPO", "SELFDIR", "LITERAL") for k in kk):
                        # substitute and keep as literal-ish
                        sv = val.strip('"\'')
                        def sub(m2):
                            r = m2.group(1) or m2.group(2)
                            return kinds.get(r, ("UNKNOWN", ""))[1] or ""
                        lit = re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)", sub, sv)
                        lit = re.sub(r"\$\([^)]*\)", "", lit)
                        new = ("LITERAL", lit.strip("/") if lit else None)
                    else:
                        new = ("UNKNOWN", None)
                elif "$(" in val or "`" in val:
                    new = ("UNKNOWN", None)
                else:
                    new = ("LITERAL", val.strip('"\''))
            if kinds.get(name) != new:
                kinds[name] = new
                changed = True
        if not changed:
            break
    return kinds


def has_cd_to_scratch(text_lines, kinds):
    for ln in text_lines:
        m = re.search(r"\bcd\s+[\"']?\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?", ln)
        if m and kinds.get(m.group(1), ("UNKNOWN",))[0] == "SCRATCH":
            return True
        if re.search(r"\bcd\s+[\"']?(/tmp|\$\(mktemp)", ln):
            return True
    return False


ARGSPLIT = re.compile(r"""'([^']*)'|"([^"]*)"|(\S+)""")


def shell_operands(text, verb):
    m = re.search(r"\b%s\b" % re.escape(verb), text)
    if not m:
        return []
    seg = text[m.end():]
    seg = re.split(r"(?:&&|\|\||[;|)]|\bthen\b|\bdo\b|\bfi\b)", seg)[0]
    ops = []
    for g in ARGSPLIT.finditer(seg):
        tok = g.group(1) or g.group(2) or g.group(3) or ""
        if not tok or tok.startswith("-") or tok.startswith(("2>", ">", "<")):
            continue
        ops.append(tok)
    return ops


def py_operand(text):
    """Argument expression of the destructive python call, as source text."""
    m = re.search(r"(shutil\.rmtree|shutil\.move|os\.remove|os\.unlink|os\.rmdir|\.unlink|\.write_text|\.write_bytes|open)\s*\(", text)
    if not m:
        return None
    i = m.end() - 1
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "(":
            depth += 1
        elif text[j] == ")":
            depth -= 1
            if depth == 0:
                return text[i + 1:j].strip()
    return text[i + 1:].strip()


def resolve_shell(tok, kinds, relfile, cd_scratch):
    """-> (kind, path_or_None)."""
    if tok is None:
        return ("UNKNOWN", None)
    t = tok.strip().strip('"\'')
    if t.startswith(("/tmp", "/var/folders", "/dev/")):
        return ("SCRATCH", None)
    if "$(mktemp" in t or "mktemp" in t:
        return ("SCRATCH", None)
    m = re.match(r"^\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?(.*)$", t)
    if m:
        name, rest = m.group(1), m.group(2)
        kind, lit = kinds.get(name, ("UNKNOWN", None))
        if kind == "SCRATCH":
            return ("SCRATCH", None)
        if kind in ("REPO", "SELFDIR", "LITERAL"):
            rest2 = re.sub(r"\$\{?[A-Za-z_][A-Za-z0-9_]*\}?", "*", rest)
            base = lit if lit is not None else ""
            p = (base.rstrip("/") + rest2) if base else rest2.lstrip("/")
            p = p.lstrip("/")
            if not p:
                return ("REPO_ROOT", None)
            return ("PATH", os.path.normpath(p))
        return ("UNKNOWN", None)
    if "$" in t:
        # embedded var somewhere other than the head
        head = t.split("$")[0]
        if head.startswith("."):
            head = os.path.normpath(os.path.join(os.path.dirname(relfile), head))
        if cd_scratch and not head.startswith(".softhouse"):
            return ("UNKNOWN", None)
        return ("PATH", os.path.normpath(head.rstrip("/") + "*")) if head else ("UNKNOWN", None)
    # pure literal
    if os.path.isabs(t):
        rp = os.path.normpath(t)
        if rp.startswith(ROOT + "/"):
            return ("PATH", os.path.relpath(rp, ROOT))
        return ("SCRATCH", None)
    if cd_scratch:
        return ("CD_SCRATCH_RELATIVE", t)
    if t.startswith(("./", "../")):
        return ("PATH", os.path.normpath(os.path.join(os.path.dirname(relfile), t)))
    return ("PATH", os.path.normpath(t))


def main():
    hits = json.load(open(os.path.join(HERE, "evidence", "10-census-hits.json")))["hits"]
    cache = {}
    rows = []
    for h in hits:
        fam = h["pattern"]
        if fam not in DESTRUCTIVE and fam not in OVERWRITE:
            continue
        rel, text = h["file"], h["text"]
        if rel not in cache:
            try:
                lines = open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace").read().splitlines()
            except OSError:
                lines = []
            k = classify_vars(rel, lines)
            cache[rel] = (k, has_cd_to_scratch(lines, k))
        kinds, cd_scratch = cache[rel]

        if fam in ("rm-rf", "rm-plain"):
            ops = shell_operands(text, "rm")
            raw_targets = ops[:1]
        elif fam == "mv":
            ops = shell_operands(text, "mv")
            raw_targets = ops[-1:] if len(ops) >= 2 else []
        elif fam == "sed-i":
            ops = shell_operands(text, "sed")
            raw_targets = ops[-1:]
        elif fam == "truncate":
            raw_targets = shell_operands(text, "truncate")[-1:]
        elif fam == "git-checkout-dd":
            m = re.search(r"git\s+checkout\s+--\s+(\S+)", text)
            raw_targets = [m.group(1)] if m else []
        elif fam == "tee":
            raw_targets = shell_operands(text, "tee")[:1]
        elif fam == "redirect":
            m = re.search(r"(?<![0-9<>&|])>(?!>)\s*(\"[^\"]+\"|'[^']+'|\S+)", text)
            raw_targets = [m.group(1)] if m else []
        else:
            raw_targets = [py_operand(text)]

        raw = raw_targets[0] if raw_targets else None

        if rel.endswith(".py"):
            # python: only literal-headed expressions are resolvable here
            if raw and re.match(r"^[\"']", raw.strip()):
                lit = re.match(r"^[\"']([^\"']+)[\"']", raw.strip()).group(1)
                kind, path = resolve_shell(lit, {}, rel, False)
            elif raw and re.search(r"(tmp|TMP|mkdtemp|TemporaryDirectory|sandbox|scratch|SCRATCH|work|WORK)", raw):
                kind, path = ("SCRATCH", None)
            else:
                kind, path = ("UNKNOWN", None)
        else:
            kind, path = resolve_shell(raw, kinds, rel, cd_scratch)

        if kind == "PATH":
            n = tracked_count(path)
            status = "TRACKED" if n > 0 else "UNTRACKED"
        elif kind == "REPO_ROOT":
            status, n = "WHOLE_REPO", -1
        elif kind == "SCRATCH":
            status, n = "SCRATCH", 0
        elif kind == "CD_SCRATCH_RELATIVE":
            status, n = "SCRATCH", 0
        else:
            status, n = "UNKNOWN", None
        rows.append({**h, "raw_target": raw, "target": path, "status": status,
                     "tracked_files": n,
                     "family": "destructive" if fam in DESTRUCTIVE else "overwrite"})

    with open(os.path.join(HERE, "evidence", "20-resolved.json"), "w") as fh:
        json.dump(rows, fh, indent=1)

    for fam in ("destructive", "overwrite"):
        sub = [r for r in rows if r["family"] == fam]
        agg = {}
        for r in sub:
            agg[r["status"]] = agg.get(r["status"], 0) + 1
        print("%s: %d operations" % (fam.upper(), len(sub)))
        for k in sorted(agg):
            print("   %-14s %5d" % (k, agg[k]))
        print()

    print("=== DESTRUCTIVE ops whose target CONTAINS TRACKED FILES ===")
    tr = [r for r in rows if r["family"] == "destructive" and r["status"] in ("TRACKED", "WHOLE_REPO")]
    tr.sort(key=lambda r: (-(r["tracked_files"] or 0), r["file"], r["line"]))
    for r in tr:
        print("%-9s %5s  %s:%s  -> %s" % (r["pattern"], r["tracked_files"], r["file"], r["line"], r["target"]))
    print("TOTAL: %d" % len(tr))

    print()
    print("=== UNKNOWN destructive operands (blind spot; listed, not dropped) ===")
    un = [r for r in rows if r["family"] == "destructive" and r["status"] == "UNKNOWN"]
    for r in un:
        print("%-9s %s:%s  raw=%r" % (r["pattern"], r["file"], r["line"], r["raw_target"]))
    print("TOTAL UNKNOWN: %d" % len(un))


if __name__ == "__main__":
    sys.exit(main())
