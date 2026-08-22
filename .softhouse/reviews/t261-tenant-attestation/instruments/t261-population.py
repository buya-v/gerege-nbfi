#!/usr/bin/env python3
"""T261 instrument -- INDEPENDENT re-derivation of T250's TERM 1 / TERM 2.

Written without reusing T250's code.  Deliberately WIDER than T250's selector so
that an UNDER-count would show up:

  * emitters: echo / printf / print   AND ALSO   <python>.write( / heredoc body
    lines.  T250's ATTEST_RE matches only echo|printf|print, so a sidecar written
    by `cat <<EOF` or by `fh.write("Key: value\n")` is INVISIBLE to it.  Both
    shapes are measured here separately and reported.
  * oracle contact: curl / psql / a literal oracle host:port.

ENGINE (P-75): python3 `re` over bytes read from disk.  No grep, no rg, no
git grep.  Population comes from a git TREE listing, and a non-zero git exit
ABORTS (exit 5).  Calibrated positive AND negative; disagreement ABORTS (exit 4).

usage: t261-population.py <tree-ish|-> <root-dir>
"""
import os
import re
import subprocess
import sys

TREE = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "-" else None
ROOT = sys.argv[2] if len(sys.argv) > 2 else "."

EMIT_QUOTED = re.compile(
    r"""(?P<cmd>echo|printf|print|write)\s*\(?\s*(?P<q>["'])"""
    r"""(?P<key>[A-Za-z][A-Za-z0-9_-]*):[ ](?P<val>[^"'\n]*?)(?P=q)"""
)
BARE_LINE = re.compile(r"^(?P<key>[A-Za-z][A-Za-z0-9_-]*):[ ](?P<val>[^\n]*)$", re.M)
HEREDOC_OPEN = re.compile(r"<<-?\s*[\"']?(?P<tag>[A-Za-z_][A-Za-z0-9_]*)[\"']?")

ASSIGN = re.compile(
    r"""^[ \t]*(?:export[ \t]+|local[ \t]+|readonly[ \t]+)?"""
    r"""(?P<n>[A-Za-z_][A-Za-z0-9_]*)="""
    r"""(?:'(?P<s>[^']*)'|"(?P<d>[^"]*)"|(?P<b>[^\s;#|&)]*))""",
    re.M,
)
SOURCE = re.compile(
    r"""^[ \t]*(?:\.|source)[ \t]+["']?(?:\$\{?\w+\}?/)?(?P<rel>[\w./-]+\.sh)""", re.M
)
ORACLE = re.compile(r"\bcurl\b|\bpsql\b|localhost:8443")


def read(p):
    with open(p, "rb") as f:
        return f.read().decode("utf-8", "replace")


def assigns(text):
    out = {}
    for m in ASSIGN.finditer(text):
        v = m.group("s")
        if v is None:
            v = m.group("d")
        if v is None:
            v = m.group("b")
        if v is None:
            continue
        out.setdefault(m.group("n"), []).append(v)
    return out


def scope_of(path, text, depth=0):
    sc = assigns(text)
    if depth >= 3:
        return sc
    base = os.path.dirname(path)
    for m in SOURCE.finditer(text):
        c = os.path.normpath(os.path.join(base, os.path.basename(m.group("rel"))))
        if os.path.isfile(c):
            for k, v in scope_of(c, read(c), depth + 1).items():
                sc.setdefault(k, []).extend(v)
    return sc


def heredoc_spans(text):
    """[(start,end)] char spans of heredoc bodies -- an emitter T250 cannot see."""
    spans = []
    lines = text.split("\n")
    offs, o = [], 0
    for line in lines:
        offs.append(o)
        o += len(line) + 1
    i = 0
    while i < len(lines):
        m = HEREDOC_OPEN.search(lines[i])
        if m:
            tag = m.group("tag")
            j = i + 1
            while j < len(lines) and lines[j].strip() != tag:
                j += 1
            if j < len(lines):
                spans.append((offs[i + 1] if i + 1 < len(offs) else o,
                              offs[j] if j < len(offs) else o))
                i = j
        i += 1
    return spans


def literal_attestations(path, text):
    hits = []
    for m in EMIT_QUOTED.finditer(text):
        k, v = m.group("key"), m.group("val")
        if not v.strip():
            continue
        if any(ch in v for ch in "$%{`"):
            continue
        hits.append((text.count("\n", 0, m.start()) + 1, k, v,
                     "quoted-emitter:" + m.group("cmd")))
    for (a, b) in heredoc_spans(text):
        seg = text[a:b]
        for m in BARE_LINE.finditer(seg):
            k, v = m.group("key"), m.group("val")
            if not v.strip():
                continue
            if any(ch in v for ch in "$%{`"):
                continue
            hits.append((text.count("\n", 0, a + m.start()) + 1, k, v, "heredoc-body"))
    return hits


def _strip_nl(val):
    """A python/printf writer usually ends the literal with a trailing \\n."""
    v = val
    while v.endswith("\\n") or v.endswith("\\r"):
        v = v[:-2]
    return v


def shadow(scope, key, val):
    val = _strip_nl(val)
    full = "%s: %s" % (key, val)
    for n, vs in sorted(scope.items()):
        for v in vs:
            if v.strip() == full:
                return (n, "full-header")
    for n, vs in sorted(scope.items()):
        for v in vs:
            if v.strip() == val.strip() and len(val.strip()) >= 3:
                return (n, "bare-value")
    return None


def calibrate():
    pos = ("T='Fineract-Platform-TenantId: gerege'\ncurl -H \"$T\" x\n"
           'echo "Fineract-Platform-TenantId: gerege" > f\n')
    neg = ("T='Fineract-Platform-TenantId: gerege'\ncurl -H \"$T\" x\n"
           'echo "$T" > f\n')
    hpos = ("T='Fineract-Platform-TenantId: gerege'\ncurl -H \"$T\" x\n"
            "cat > f <<EOF\nFineract-Platform-TenantId: gerege\nEOF\n")
    wpos = ("T='Fineract-Platform-TenantId: gerege'\nsubprocess.run(['curl','-H',T])\n"
            "fh.write('Fineract-Platform-TenantId: gerege\\n')\n")
    wneg = ("T='Fineract-Platform-TenantId: gerege'\nsubprocess.run(['curl','-H',T])\n"
            "fh.write(T + '\\n')\n")
    ok = True
    for name, src, want in (("positive/echo", pos, 1), ("negative/echo-var", neg, 0),
                            ("positive/heredoc", hpos, 1), ("positive/py-write", wpos, 1),
                            ("negative/py-write-var", wneg, 0)):
        sc = assigns(src)
        n = len([h for h in literal_attestations("x.sh", src) if shadow(sc, h[1], h[2])])
        print("CALIBRATION %-22s expected %d flagged, got %d" % (name, want, n))
        if n != want:
            ok = False
    if not ok:
        sys.stderr.write("CALIBRATION FAILED -- ABORT\n")
        sys.exit(4)
    print("CALIBRATION OK: arms differ by exactly the defect; instrument discriminates.\n")


def main():
    calibrate()
    if TREE:
        p = subprocess.run(["git", "ls-tree", "-r", "--name-only", TREE],
                           capture_output=True, text=True)
    else:
        p = subprocess.run(["git", "ls-files"], capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write("ABORT: git listing failed rc=%d %s\n" % (p.returncode, p.stderr))
        sys.exit(5)
    tracked = p.stdout.splitlines()
    scripts = [x for x in tracked if x.endswith(".sh") or x.endswith(".py")]
    term1, term2, skipped, byemitter = [], [], [], {}
    for rel in scripts:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            skipped.append(rel)
            continue
        text = read(path)
        hits = literal_attestations(path, text)
        anyattest = bool(EMIT_QUOTED.search(text)) or bool(hits)
        if not anyattest:
            continue
        if not ORACLE.search(text):
            continue
        term1.append(rel)
        sc = scope_of(path, text)
        fl = [(l, k, v, how) + shadow(sc, k, v)
              for (l, k, v, how) in hits if shadow(sc, k, v)]
        if fl:
            term2.append((rel, fl))
            for f in fl:
                kind = f[3].split(":")[0]
                byemitter[kind] = byemitter.get(kind, 0) + 1
    print("SCOPE  tree=%s root=%s" % (TREE or "<index>", os.path.realpath(ROOT)))
    print("tracked                 : %d" % len(tracked))
    print("  .sh/.py               : %d" % len(scripts))
    print("  absent on disk (skip) : %d" % len(skipped))
    for s in skipped:
        print("      SKIPPED %s" % s)
    print("")
    print("TERM 1  oracle-talking scripts emitting >=1 `Key: value` attestation : %d"
          % len(term1))
    for x in term1:
        print("    %s" % x)
    print("")
    print("TERM 2  of those, >=1 LITERAL attestation shadowed by an in-scope var: %d"
          % len(term2))
    for rel, fl in term2:
        print("    %s" % rel)
        for (l, k, v, how, var, kind) in fl:
            print("        line %-5d %-34s = %-34s <- $%s (%s) [%s]"
                  % (l, k, v, var, kind, how))
    print("")
    print("emitter breakdown of flagged lines: %s" % byemitter)
    print("RATE: %d / %d" % (len(term2), len(term1)))


main()
